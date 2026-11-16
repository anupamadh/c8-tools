"""Part 1: your first tool call.  Run: python tool_call.py
The steps are in README.md. Each one adds a few lines to the bottom of this file."""
import csv, io, json, os, sys
import requests
from dotenv import load_dotenv

load_dotenv()
if not os.environ.get("GROQ_API_KEY"):
    raise SystemExit("No GROQ_API_KEY found. Make a file called .env next to tool_call.py with one line: GROQ_API_KEY=your key")

# ---------- THE SHEET (given) ----------
# Plain code, no model: one lecture of the course sheet, looked up by its number.
SHEET = "https://docs.google.com/spreadsheets/d/1Kg6T-dJWaYx_JCPiRk3u0nBuAQcsCVRDPj1NFKP4WzM/gviz/tq?tqx=out:csv&headers=0&gid=368290478"

def get_lecture(number):
    for row in csv.reader(io.StringIO(requests.get(SHEET).text)):
        if row[1].startswith(f"{number}. "):
            return {"date": row[0], "title": row[1], "type": row[2], "tools": row[3]}
    return {"error": f"There is no lecture {number}. Lectures run from 1 to 19."}

ITINERARY = "https://docs.google.com/spreadsheets/d/1b5zDSCA7XX4NmVQZKdEzKumQJAaVBodMc-Vm3UwUniU/export?format=csv&gid=0"

def get_itinerary(date):
    plan = []
    for row in csv.reader(io.StringIO(requests.get(ITINERARY).text)):
        if row and row[0].strip().lower() == date.strip().lower():
            plan.append({"day": row[1], "time": row[2], "activity": row[3], "description": row[5]})
    if plan:
        return {"date": date, "plan": plan}
    return {"error": f"Nothing is planned for {date}. The trip runs from 1 Jan 2027 to 4 Jan 2027."}

itinerary_card = {
    "type": "function",
    "function": {
        "name": "get_itinerary",
        "description": (
            "Returns the Kuching, Sarawak trip plan for one day: the day, time, activity "
            "and description of everything planned, including alternative options. "
            "Use it when someone asks what is planned on a specific trip date. "
            "Not for general questions about Sarawak."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "The trip date written like the sheet, e.g. 1 Jan 2027. The trip runs 1 to 4 Jan 2027."
                }
            },
            "required": ["date"]
        }
    }
}

# ---------- THE MODEL (given) ----------
# One message to Groq, one message back. Nothing is added that you do not send.
def ask_model(messages, tools=None):
    body = {"model": "openai/gpt-oss-120b", "messages": messages}
    if tools:
        body["tools"] = tools
    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                      headers={"Authorization": "Bearer " + os.environ["GROQ_API_KEY"]}, json=body)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]

# ---------- YOUR SERVER (yours to write) ----------
# python tool_call.py                      asks the question below
# python tool_call.py "What is an API?"    asks your own
question = " ".join(sys.argv[1:]) or "When is Lecture 12 of 100xEngineers Cohort 8, and what is it about?"
messages = [{"role": "user", "content": question}]

# Step 2. The card: fill in the two empty strings.
card = {"type": "function", "function": {
    "name": "get_lecture",
    "description": "Returns one lecture of the 100xEngineers Cohort 8 curriculum: its date, title, type and tools. Use it when someone asks about a specific lecture by number. Not for general questions.",                                                    # Use it when
    "parameters": {"type": "object",
                   "properties": {"number": {"type": "integer",
                                             "description": "The lecture number, 1 to 19."}},         # It needs
                   "required": ["number"]},
}}
CARDS = [card, itinerary_card]
reply = ask_model(messages, CARDS)                 # Step 2: send the cards too
print(json.dumps(reply, indent=2, ensure_ascii=False))

# Step 3. Run the request the model wrote.
# call = reply["tool_calls"][0]
# # To retrieve the arguments key and convert the arguments from text to disctionary, use the following code:
# args = json.loads(call["function"]["arguments"])
# #pass the arguments to the get_lecture function as a key-value pair and store the result in a variable called result
# result = get_lecture(**args)
# print(result)

# Step 4. Hand the result back to the model and print its answer.
#Add the model's request to messages i.e the card
# messages.append(reply)
# #Add the result of the tool call to messages
# messages.append({"role": "tool", "tool_call_id": call["id"], "content": json.dumps(result)})
# #Call ask_model again with the updated messages and store the result in a variable called reply2
# #This sends the full conversation back to the model. Now that it can see the row, it writes a normal answer instead of another request.
# reply2 = ask_model(messages, [card])
# #Print the content of reply2
# print(reply2["content"])


# Step 5. Turn steps 3 and 4 into a loop.
TOOLS = {"get_lecture": get_lecture, "get_itinerary": get_itinerary}


reply = ask_model(messages, CARDS)

while reply.get("tool_calls"):
    messages.append(reply)
    for call in reply["tool_calls"]:
        name = call["function"]["name"]
        args = json.loads(call["function"]["arguments"])
        print("The model asked for:", name, args)
        result = TOOLS[name](**args)
        messages.append({"role": "tool", "tool_call_id": call["id"], "content": json.dumps(result)})
    reply = ask_model(messages, CARDS)

print("\n" + reply["content"])

