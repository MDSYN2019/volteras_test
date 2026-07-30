"""Continuously ingest vehicle CSV files into the application PostgreSQL table."""

from __future__ import annotations

import argparse
import os
from collections.abc import Iterator

import psycopg
from pyspark.sql import DataFrame, Row, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, StringType, StructField, StructType


CSV_SCHEMA = StructType(
    [
        StructField("timestamp", StringType(), False),
        StructField("speed", StringType(), True),
        StructField("odometer", DoubleType(), False),
        StructField("soc", DoubleType(), False),
        StructField("elevation", DoubleType(), False),
        StructField("shift_state", StringType(), True),
    ]
)

INSERT_SQL = """
    insert into vehicle_data
        (vehicle_id, timestamp, speed, odometer, soc, elevation, shift_state)
    values (%s, %s, %s, %s, %s, %s, %s)
    on conflict (vehicle_id, timestamp) do nothing
"""


def write_partition(rows: Iterator[Row]) -> None:
    """Upsert one Spark partition with a single database transaction."""
    database_url = os.environ.get(
        "STREAM_DATABASE_URL", "postgresql://volteras:volteras@localhost:5432/volteras"
    )
    values = [
        (
            row.vehicle_id,
            row.observed_at,
            row.speed,
            row.odometer,
            row.soc,
            row.elevation,
            row.shift_state,
        )
        for row in rows
    ]
    if not values:
        return
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.executemany(INSERT_SQL, values)


def process_batch(batch: DataFrame, batch_id: int) -> None:
    """Report rejected records and persist valid records idempotently."""
    batch.persist()
    try:
        invalid_count = batch.filter(~F.col("_is_valid")).count()
        valid = batch.filter(F.col("_is_valid")).drop("_is_valid")
        valid_count = valid.count()
        print(f"batch={batch_id} valid={valid_count} rejected={invalid_count}", flush=True)
        valid.foreachPartition(write_partition)
    finally:
        batch.unpersist()


def build_stream(spark: SparkSession, input_path: str) -> DataFrame:
    """Build the typed stream and derive vehicle IDs from CSV filenames."""
    null_tokens = ["", "NULL", "NONE", "N/A"]
    raw = (
        spark.readStream.schema(CSV_SCHEMA)
        .option("header", True)
        .option("mode", "PERMISSIVE")
        .csv(input_path)
    )
    speed_text = F.upper(F.trim(F.col("speed")))
    shift_text = F.upper(F.trim(F.col("shift_state")))
    typed = raw.select(
        F.regexp_extract(F.input_file_name(), r"([^/]+)\.csv$", 1).alias("vehicle_id"),
        F.coalesce(
            F.to_timestamp("timestamp", "yyyy-MM-dd HH:mm:ss.SSS"),
            F.to_timestamp("timestamp", "yyyy-MM-dd'T'HH:mm:ss.SSSXXX"),
        ).alias("observed_at"),
        F.when(speed_text.isin(null_tokens), None)
        .otherwise(F.col("speed").cast("double"))
        .alias("speed"),
        "odometer",
        "soc",
        "elevation",
        F.when(shift_text.isin(null_tokens), None).otherwise(shift_text).alias("shift_state"),
    )
    return typed.withColumn(
        "_is_valid",
        (F.length("vehicle_id") > 0)
        & F.col("observed_at").isNotNull()
        & F.col("odometer").isNotNull()
        & F.col("soc").between(0, 100)
        & F.col("elevation").isNotNull(),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="sample_data", help="Directory receiving CSV files")
    parser.add_argument(
        "--checkpoint", default=".checkpoints/vehicle-stream", help="Durable checkpoint directory"
    )
    args = parser.parse_args()

    spark = SparkSession.builder.appName("volteras-vehicle-ingestion").getOrCreate()
    spark.conf.set("spark.sql.session.timeZone", "UTC")
    query = (
        build_stream(spark, args.input)
        .writeStream.foreachBatch(process_batch)
        .option("checkpointLocation", args.checkpoint)
        .trigger(processingTime="10 seconds")
        .start()
    )
    query.awaitTermination()


if __name__ == "__main__":
    main()
