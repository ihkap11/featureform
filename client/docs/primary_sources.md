# Primary Sources

## Tables

Tables can be registered off of any [SQL database](providers.md). Supported databases are: BigQuery, Postgres, Redshift, ClickHouse and Snowflake.

::: featureform.register.OfflineSQLProvider.register_table
    handler: python
    options:
        show_root_heading: false
        show_source: false
        show_root_toc_entry: false

## Files

Files can be registered from the Local, Spark, and Kubernetes providers. Supported file types are: CSV and Parquet.

### Spark

Sparkmode can register single files.

::: featureform.register.OfflineSparkProvider.register_file
    handler: python
    options:
        show_root_heading: false
        show_source: false
        show_root_toc_entry: false

### Kubernetes Pandas Runner

::: featureform.register.OfflineK8sProvider.register_file
    handler: python
    options:
        show_root_heading: false
        show_source: false
        show_root_toc_entry: false
