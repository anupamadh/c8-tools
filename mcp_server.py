"""Part 2: the same tool on the sheet's side, as an MCP server.  Run: python mcp_server.py
The steps are in README.md."""
import csv, io, socket
from typing import Annotated
import requests
from fastmcp import FastMCP

SHEET = "https://docs.google.com/spreadsheets/d/1Kg6T-dJWaYx_JCPiRk3u0nBuAQcsCVRDPj1NFKP4WzM/gviz/tq?tqx=out:csv&headers=0&gid=368290478"

mcp = FastMCP("100x curriculum")

# Step 1. Move get_lecture here from tool_call.py and put @mcp.tool on the line above it.
# Step 2. Write the card into the function itself: a docstring and a type hint.
@mcp.tool
def get_lecture(number: Annotated[int, "The lecture number, 1 to 19."]) -> dict:
    """Returns one lecture from the 100xEngineers Cohort 8 schedule: its date, title,
    type and tools. Use it when someone asks about a specific lecture or class.
    Not for general questions."""
    for row in csv.reader(io.StringIO(requests.get(SHEET).text)):
        if row[1].startswith(f"{number}. "):
            return {"date": row[0], "title": row[1], "type": row[2], "tools": row[3]}
    return {"error": f"There is no lecture {number}. Lectures run from 1 to 19."}


ITINERARY = "https://docs.google.com/spreadsheets/d/1b5zDSCA7XX4NmVQZKdEzKumQJAaVBodMc-Vm3UwUniU/export?format=csv&gid=0"

@mcp.tool
def get_itinerary(date: Annotated[str, "The trip date written like the sheet, e.g. 1 Jan 2027. The trip runs 1 to 4 Jan 2027."]) -> dict:
    """Returns the Kuching, Sarawak trip plan for one day: the day, time, activity
    and description of everything planned, including alternative options.
    Use it when someone asks what is planned on a specific trip date.
    Not for general questions about Sarawak."""
    plan = []
    for row in csv.reader(io.StringIO(requests.get(ITINERARY).text)):
        if row and row[0].strip().lower() == date.strip().lower():
            plan.append({"day": row[1], "time": row[2], "activity": row[3], "description": row[5]})
    if plan:
        return {"date": date, "plan": plan}
    return {"error": f"Nothing is planned for {date}. The trip runs from 1 Jan 2027 to 4 Jan 2027."}

# Any app can now reach it at http://localhost:8000/mcp
if __name__ == "__main__":
    if socket.socket().connect_ex(("127.0.0.1", 8000)) == 0:
        raise SystemExit("Port 8000 is already in use, probably by a server you started earlier. "
                         "Stop it with Ctrl+C in its terminal, or run: kill $(lsof -t -i:8000)")
    mcp.run(transport="http", port=8000)
