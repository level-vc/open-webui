"""
title: Level Engineer
author: Level VC
author_url: https://levelvc.com
version: 1.1.0
description: Allows the agent to query RDS and Athena for our data

Configuration:
- Configure the API key through the Open WebUI tool configuration interface
"""

import requests
from pydantic import BaseModel, Field


async def _emit_event(
    event_emitter, event_type: str, description: str, done: bool = False
):
    """Helper function to safely emit events."""
    if event_emitter:
        try:
            await event_emitter(
                {
                    "type": event_type,
                    "data": {"description": description, "done": done, "hidden": False},
                }
            )
        except Exception:
            # Silently ignore event emission errors to not break the tool
            pass


def _make_api_request(
    method: str, endpoint: str, data: dict = None, valves=None
) -> dict:
    """Make authenticated API request to LVC API."""
    url = f"https://api.lvcdev.com{endpoint}"
    headers = {
        "Authorization": f"Bearer {valves.api_key}",
        "Content-Type": "application/json",
    }

    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            return {"error": f"Unsupported HTTP method: {method}"}

        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}


class Tools:
    def __init__(self):
        """Initialize the Tool."""
        self.valves = self.Valves()

    class Valves(BaseModel):
        api_key: str = Field("", description="Your Level VC API key")

    async def read_athena_query(
        self,
        query: str,
        __event_emitter__=None,
    ) -> str:
        """
        Execute SQL queries against Athena/Presto and return results.

        Use this tool to query Level's data warehouse using Athena/Presto SQL.
        The results include data, columns, and row count information.

        Recommend using LIMIT clauses to avoid overwhelming responses.

        Args:
            query: The SQL query to execute against Athena/Presto

        Returns:
            JSON string with query results including 'data' (records),
            'columns' (column names), and 'row_count'
        """
        # Emit start event
        query_preview = query[:100] + "..." if len(query) > 100 else query
        await _emit_event(
            __event_emitter__,
            "status",
            f"🔍 Executing Athena query: {query_preview}",
            done=False,
        )

        data = {"query": query}

        result = _make_api_request("POST", "/engineer/read-athena-query", data, self.valves)

        # Emit completion event
        if isinstance(result, dict) and "error" in result:
            await _emit_event(
                __event_emitter__,
                "status",
                f"❌ Athena query failed: {result.get('error', 'Unknown error')}",
                done=True,
            )
        else:
            row_count = (
                result.get("row_count", "unknown")
                if isinstance(result, dict)
                else "unknown"
            )
            await _emit_event(
                __event_emitter__,
                "status",
                f"✅ Athena query completed - returned {row_count} rows",
                done=True,
            )

        return result

    async def read_rds_query(
        self,
        query: str,
        __event_emitter__=None,
    ) -> str:
        """
        Execute SQL queries against PostgreSQL RDS and return results.

        Use this tool to query Level's PostgreSQL database for transactional data.
        The results include data, columns, and row count information.

        Recommend using LIMIT clauses to avoid overwhelming responses.

        Args:
            query: The SQL query to execute against PostgreSQL RDS

        Returns:
            JSON string with query results including 'data' (records),
            'columns' (column names), and 'row_count'
        """
        # Emit start event
        query_preview = query[:100] + "..." if len(query) > 100 else query
        await _emit_event(
            __event_emitter__,
            "status",
            f"🐘 Executing PostgreSQL query: {query_preview}",
            done=False,
        )

        data = {"query": query}

        result = _make_api_request("POST", "/engineer/read-rds-query", data, self.valves)

        # Emit completion event
        if isinstance(result, dict) and "error" in result:
            await _emit_event(
                __event_emitter__,
                "status",
                f"❌ PostgreSQL query failed: {result.get('error', 'Unknown error')}",
                done=True,
            )
        else:
            row_count = (
                result.get("row_count", "unknown")
                if isinstance(result, dict)
                else "unknown"
            )
            await _emit_event(
                __event_emitter__,
                "status",
                f"✅ PostgreSQL query completed - returned {row_count} rows",
                done=True,
            )

        return result

    async def get_athena_table_info(
        self,
        table_name: str,
        __event_emitter__=None,
    ) -> str:
        """
        Get detailed schema information and sample data for Athena/Presto/Trino tables.

        Use this tool to understand table structure before writing queries.
        Returns column details, data types, sample values, and sample records.

        Args:
            table_name: Table name in format 'database.table' (e.g., 'my_db.my_table')

        Returns:
            JSON string with table schema information including:
            - columns: Array of column details (name, type, nullable, etc.)
            - sample_data: Sample records from the table
            - database and table name information
        """
        # Emit start event
        await _emit_event(
            __event_emitter__,
            "status",
            f"📊 Fetching table schema for {table_name}",
            done=False,
        )

        data = {"table_name": table_name}

        result = _make_api_request("POST", "/engineer/get-athena-table-info", data, self.valves)

        # Emit completion event
        if isinstance(result, dict) and "error" in result:
            await _emit_event(
                __event_emitter__,
                "status",
                f"❌ Failed to fetch table info: {result.get('error', 'Unknown error')}",
                done=True,
            )
        else:
            columns_count = (
                len(result.get("columns", []))
                if isinstance(result, dict)
                else "unknown"
            )
            await _emit_event(
                __event_emitter__,
                "status",
                f"✅ Successfully fetched schema for {table_name} - {columns_count} columns",
                done=True,
            )

        return result
