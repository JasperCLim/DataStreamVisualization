import os
import time

import matplotlib.pyplot as plt
import pandas as pd
import psycopg


class StreamingSimulator:
    def __init__(self, data, database_url=None):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("data must be a pandas DataFrame")

        self.data = data.copy()
        self.database_url = database_url or os.environ["DATABASE_URL"]
        self.position = 0

    def initialize_database(self):
        with psycopg.connect(self.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS robot_readings (
                        id BIGSERIAL PRIMARY KEY,
                        trait TEXT NOT NULL,
                        axis_1 DOUBLE PRECISION,
                        axis_2 DOUBLE PRECISION,
                        axis_3 DOUBLE PRECISION,
                        axis_4 DOUBLE PRECISION,
                        axis_5 DOUBLE PRECISION,
                        axis_6 DOUBLE PRECISION,
                        axis_7 DOUBLE PRECISION,
                        axis_8 DOUBLE PRECISION,
                        axis_9 DOUBLE PRECISION,
                        axis_10 DOUBLE PRECISION,
                        axis_11 DOUBLE PRECISION,
                        axis_12 DOUBLE PRECISION,
                        axis_13 DOUBLE PRECISION,
                        axis_14 DOUBLE PRECISION,
                        reading_time TIMESTAMPTZ NOT NULL
                    )
                """)

    def nextDataPoint(self, plot=True, delay_seconds=0):
        if self.position >= len(self.data):
            return None

        row = self.data.iloc[self.position].copy()
        self.position += 1
        values = [
            row.get("Trait"),
            *[row.get(f"Axis #{axis}") for axis in range(1, 15)],
            row.get("Time"),
        ]

        with psycopg.connect(self.database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO robot_readings (
                        trait, axis_1, axis_2, axis_3, axis_4, axis_5, axis_6, axis_7,
                        axis_8, axis_9, axis_10, axis_11, axis_12, axis_13, axis_14,
                        reading_time
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    values,
                )
                reading_id = cursor.fetchone()[0]

        if plot:
            axis_values = pd.to_numeric(row.filter(like="Axis #"), errors="coerce")
            axis_values.plot(kind="bar", title=f"Robot reading {reading_id}")
            plt.xlabel("Axis")
            plt.ylabel("Current")
            plt.tight_layout()
            plt.show()

        if delay_seconds:
            time.sleep(delay_seconds)
        return row.to_frame().T