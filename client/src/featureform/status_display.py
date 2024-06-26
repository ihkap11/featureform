import sys
import time
from typing import List, Tuple, Type

from dataclasses import dataclass
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.text import Text

from featureform.grpc_client import GrpcClient
from featureform.resources import (
    ErrorInfo,
    FeatureVariant,
    LabelVariant,
    OnDemandFeatureVariant,
    Provider,
    Resource,
    SourceVariant,
    TrainingSetVariant,
)

# maximum number of dots printing when featureform apply for Running...
MAX_NUM_RUNNING_DOTS = 10
SECONDS_BETWEEN_STATUS_CHECKS = 2


def display_statuses(grpc_client: GrpcClient, resources: List[Resource], verbose=False):
    StatusDisplayer(grpc_client, resources, verbose=verbose).display()


@dataclass
class DisplayStatus:
    resource_type: Type
    name: str
    variant: str
    status: str = "NO_STATUS"
    error: str = None
    has_health_check: bool = False

    def is_finished(self) -> bool:
        return (
            self.status == "READY"
            or self.status == "FAILED"
            or (
                self.resource_type is Provider
                and self.status == "NO_STATUS"
                and not self.has_health_check
            )  # Provider is a special case
        )

    @staticmethod
    def from_resource(resource: Resource):
        variant = getattr(resource, "variant", "")
        return DisplayStatus(
            resource_type=type(resource),
            name=resource.name,
            variant=variant,
            status=resource.status,
            error=resource.error,
            has_health_check=bool(getattr(resource, "has_health_check", False)),
        )


class StatusDisplayer:
    did_error: bool = False
    RESOURCE_TYPES_TO_CHECK = {
        FeatureVariant,
        OnDemandFeatureVariant,
        TrainingSetVariant,
        LabelVariant,
        SourceVariant,
        Provider,
    }

    STATUS_TO_COLOR = {
        "READY": "green",
        "CREATED": "green",
        "PENDING": "yellow",
        "NO_STATUS": "white",
        "FAILED": "red",
    }

    def __init__(
        self, grpc_client: GrpcClient, resources: List[Resource], verbose=False
    ):
        self.verbose = verbose
        filtered_resources = filter(
            lambda r: any(
                isinstance(r, resource_type)
                for resource_type in self.RESOURCE_TYPES_TO_CHECK
            ),
            resources,
        )
        self.grpc_client = grpc_client

        # A more intuitive way to is to store OrderedDict[Resource, DisplayStatus] but you can't hash Resource easily
        self.resource_to_status_list: List[Tuple[Resource, DisplayStatus]] = []

        for r in filtered_resources:
            self.resource_to_status_list.append((r, DisplayStatus.from_resource(r)))

    def update_display_statuses(self):
        for resource, display_status in self.resource_to_status_list:
            if resource.name == "local-mode":
                continue
            if not display_status.is_finished():
                r = resource.get(self.grpc_client)
                server_status = r.server_status
                display_status.status = server_status.status
                if server_status.error_info is not None:
                    display_status.error = self._format_error_info(
                        server_status.error_info
                    )
                else:
                    display_status.error = r.error

    @staticmethod
    def _format_error_info(error_info: ErrorInfo):
        message = error_info.message
        reason = error_info.reason
        metadata = error_info.metadata

        formatted_metadata = "\n".join(
            [f"{key}: {value}" for key, value in metadata.items()]
        )

        return f"{reason}: {message}\n{formatted_metadata}"

    def all_statuses_finished(self) -> bool:
        return all(status.is_finished() for _, status in self.resource_to_status_list)

    def create_error_message(self):
        message = ""
        for _, status in self.resource_to_status_list:
            name = status.name
            message += f"{name}: {status.status} - {status.error}\n"
        return message

    def display(self):
        if not self.resource_to_status_list:
            return

        print()
        console = Console()
        with Live(console=console, auto_refresh=True, screen=False) as live:
            i = 0
            while True:
                self.update_display_statuses()
                finished_running = self.all_statuses_finished()

                dots = "." * (1 + i % MAX_NUM_RUNNING_DOTS)

                title = (
                    f"[green]COMPLETED[/]"
                    if finished_running
                    else f"[yellow]RUNNING{dots}[/]"
                )
                table = Table(
                    title=title,
                    title_justify="left",
                    show_header=True,
                    header_style="bold",
                    box=None,
                )

                no_table = False
                if len(self.resource_to_status_list) == 1:
                    status = self.resource_to_status_list[0][1]
                    if status.name == "local-mode":
                        no_table = True

                if not no_table:
                    table.add_column("Resource Type", width=25)
                    table.add_column("Name (Variant)", width=50, no_wrap=True)
                    table.add_column("Status", width=10)
                    table.add_column("Error", style="red")

                    for resource, status in self.resource_to_status_list:
                        error = f" {status.error}" if status.error else ""
                        if status.name == "local-mode":
                            continue
                        resource_type = status.resource_type.__name__
                        if (
                            isinstance(resource, SourceVariant)
                            and resource.is_transformation_type()
                        ):
                            resource_type = "Transformation"
                        name = status.name
                        status_text = (
                            status.status
                            if status.resource_type is not Provider
                            or status.has_health_check
                            else "CREATED"
                        )

                        table.add_row(
                            Text(resource_type),
                            Text(f"{name} ({status.variant})"),
                            Text(status_text, style=self.STATUS_TO_COLOR[status_text]),
                            Text(error, style="red"),
                        )

                live.update(table)
                live.refresh()

                if finished_running:
                    # This block is used for testing
                    # Tests check for both stderr and an exception
                    # If we don't throw an exception, then tests will pass even when things fail to register
                    # We also print all the error messages because the table does not get saved when
                    # capturing stdout/stderr
                    if self.verbose and self.did_error:
                        statuses = self.create_error_message()
                        sys.tracebacklimit = 0
                        raise Exception("Some resources failed to create\n" + statuses)
                    break

                i += 1
                time.sleep(SECONDS_BETWEEN_STATUS_CHECKS)
