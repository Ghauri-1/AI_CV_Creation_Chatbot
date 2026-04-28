import os
import json
from openai import OpenAI, BadRequestError
from dotenv import load_dotenv

load_dotenv()

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.storage.test_db import (
    dbb, Conversations, Messages,
    Experience, Education, Projects,
    Activites_and_Interests, References,
)
from backend.services.tools import get_data, add_data, update_data, delete_data


# ── Configuration ──────────────────────────────────────────────────────────────

MODEL = os.environ.get("NVIDIA_MODEL", "z-ai/glm5")
HISTORY_LIMIT = int(os.environ.get("AGENT_HISTORY_LIMIT", "40"))
USE_NATIVE_TOOLS = os.environ.get("AGENT_USE_NATIVE_TOOLS", "true").lower() != "false"

_client = OpenAI(
    api_key=os.environ.get("NVIDIA_API_KEY"),
    base_url="https://integrate.api.nvidia.com/v1",
)

TABLE_MAP = {
    "Experience":              Experience,
    "Education":               Education,
    "Projects":                Projects,
    "Activites_and_Interests": Activites_and_Interests,
    "References":              References,
}

# ── System prompts ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert CV builder assistant. Your job is to help the user collect, organise, and refine their career information so it can be formatted into a professional CV.

You have access to the user's CV database through four tools: get_cv_data, add_cv_data, update_cv_data, and delete_cv_data. Each operates on one of five sections: Experience, Education, Projects, Activites_and_Interests, References.

Guidelines:
- Greet the user and ask what they want to work on if they have not specified.
- Before adding data, confirm the detail with the user.
- When updating or deleting, always call get_cv_data first to find the correct row_id.
- Keep project details concise (under 350 characters) to fit database constraints.
- After completing a database action, confirm to the user what was saved.
- If a tool call returns success=false, tell the user politely and ask them to clarify.
- Never invent CV data — only save what the user explicitly tells you."""

# Fallback when the model does not support native tool calling
TOOL_PROMPT_SUFFIX = """

You also have access to four functions. To call a function, respond ONLY with a JSON object on its own line in this exact format (no other text before or after):
{"tool": "<function_name>", "args": {<arguments>}}

Available functions:
- get_cv_data: args = {"table": "<section>"}
- add_cv_data: args = {"table": "<section>", "detail": "<text>"}
- update_cv_data: args = {"table": "<section>", "row_id": <int>, "detail": "<text>"}
- delete_cv_data: args = {"table": "<section>", "row_id": <int>}

table must be one of: Experience, Education, Projects, Activites_and_Interests, References

If you do not need to call a function, respond in plain text as normal."""



# ── OpenAI tool definitions ────────────────────────────────────────────────────



TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_cv_data",
            "description": (
                "Retrieve all stored entries for a given CV section for the current user. "
                "Returns a list with 'row_id' and 'detail' for each entry. "
                "Always call this before updating or deleting to find the correct row_id."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "enum": list(TABLE_MAP.keys()),
                        "description": "The CV section to read from.",
                    }
                },
                "required": ["table"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_cv_data",
            "description": (
                "Add a new entry to a CV section. Use when the user provides new information "
                "to store (e.g. a new job, qualification, or project). "
                "For Projects, keep detail under 350 characters."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "enum": list(TABLE_MAP.keys()),
                        "description": "The CV section to add an entry to.",
                    },
                    "detail": {
                        "type": "string",
                        "description": "The text content to store.",
                    },
                },
                "required": ["table", "detail"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_cv_data",
            "description": (
                "Update an existing entry in a CV section. "
                "Update or change an existing entry in a CV section. "
            "Use this when the user wants to: change, replace, fix, correct, rewrite, "
            "modify, edit, or improve something already saved. "
            "Also use when user says things like 'make it say...', 'change that to...', "
            "'actually it should be...', 'I meant...', 'that's wrong, it should be...'. "
            "You must know the row_id before calling this — use get_cv_data first."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "enum": list(TABLE_MAP.keys()),
                        "description": "The CV section to update.",
                    },
                    "row_id": {
                        "type": "integer",
                        "description": "The row_id of the entry to update, from get_cv_data.",
                    },
                    "detail": {
                        "type": "string",
                        "description": "The new text content to replace the old entry.",
                    },
                },
                "required": ["table", "row_id", "detail"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_cv_data",
            "description": (
                "Delete an existing entry from a CV section. "
                "Use get_cv_data first to find row_id. Always confirm with the user before deleting."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "enum": list(TABLE_MAP.keys()),
                        "description": "The CV section to delete from.",
                    },
                    "row_id": {
                        "type": "integer",
                        "description": "The row_id of the entry to delete.",
                    },
                },
                "required": ["table", "row_id"],
            },
        },
    },
]




# ── DB helpers ─────────────────────────────────────────────────────────────────


def get_or_create_conversation(user_id: int) -> Conversations:
    conv = (
        Conversations.query
        .filter_by(user_id=user_id)
        .order_by(Conversations.created_at.desc())
        .first()
    )


    if not conv:
        conv = Conversations(user_id=user_id, title="CV Chat")
        dbb.session.add(conv)
        dbb.session.commit()
    return conv


def load_history(conv: Conversations, limit: int = HISTORY_LIMIT) -> list:
    msgs = (
        Messages.query
        .filter_by(conv_id=conv.conv_id)
        .order_by(Messages.timestamp.asc())
        .all()
    )


    # Keep only user/assistant messages and apply limit
    history = [
        {"role": m.role, "content": m.detail}
        for m in msgs
        if m.role in ("user", "assistant")
    ]
    return history[-limit:]


def save_message(conv: Conversations, role: str, content: str) -> None:
    msg = Messages(conv_id=conv.conv_id, role=role, detail=content)
    dbb.session.add(msg)
    dbb.session.commit()


# ── Tool dispatch ──────────────────────────────────────────────────────────────



def dispatch_tool_call(tool_name: str, args: dict, user_email: str) -> str:

    table_class = TABLE_MAP.get(args.get("table", ""))

    if table_class is None:

        return json.dumps({"success": False, "data": "Unknown table name."})

    try:
        if tool_name == "get_cv_data":
            ok, data = get_data(user_email, table_class)

        elif tool_name == "add_cv_data":
            detail = args.get("detail", "")

            
            # Guard Projects.detail String(400) column
            
            if args.get("table") == "Projects" and len(detail) > 399:
                detail = detail[:399]
            ok, data = add_data(user_email, table_class, detail)

        elif tool_name == "update_cv_data":
            detail = args.get("detail", "")
            if args.get("table") == "Projects" and len(detail) > 399:
                detail = detail[:399]
            ok, data = update_data(user_email, table_class, args["row_id"], detail)

        elif tool_name == "delete_cv_data":
            ok, data = delete_data(user_email, table_class, args["row_id"])

        else:
            return json.dumps({"success": False, "data": "Unknown tool."})

        return json.dumps({"success": ok, "data": data})

    except Exception as e:
        dbb.session.rollback()
        return json.dumps({"success": False, "data": f"Tool error: {str(e)}"})



# ── Fallback: prompt-engineering tool loop ─────────────────────────────────────


def _run_agent_fallback(messages: list, user_email: str, conv: Conversations) -> str:
    """Used when the model does not support native tool calling."""


    system = messages[0]["content"] + TOOL_PROMPT_SUFFIX
    
    msgs = [{"role": "system", "content": system}] + messages[1:]

    for _ in range(8):
        response = _client.chat.completions.create(
            model=MODEL,
            messages=msgs,
        )

        content = (response.choices[0].message.content or "").strip()

        # Check if the model output a tool-call JSON
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict) and "tool" in parsed and "args" in parsed:
                result_str = dispatch_tool_call(parsed["tool"], parsed["args"], user_email)
                msgs.append({"role": "assistant", "content": content})
                msgs.append({"role": "user", "content": f"Tool result: {result_str}"})
                continue
        except (json.JSONDecodeError, TypeError):
            pass

        # Plain text reply — we're done
        reply = content or "I'm not sure how to respond to that. Could you rephrase?"
        save_message(conv, "assistant", reply)
        return reply

    fallback = "I couldn't complete that request. Please try again."
    save_message(conv, "assistant", fallback)
    return fallback


# ── Main entry point ───────────────────────────────────────────────────────────

def run_agent(user_email: str, user_id: int, user_message: str) -> str:





    conv = get_or_create_conversation(user_id)
    
    history = load_history(conv)

    save_message(conv, "user", user_message)



    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    messages += history

    messages.append({"role": "user", "content": user_message})




    # Try native tool calling first
    if USE_NATIVE_TOOLS:
        try:
            for _ in range(8):
                
                response = _client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                )

                
                choice = response.choices[0]

                if choice.finish_reason == "tool_calls":
                    assistant_msg = choice.message
                    messages.append(assistant_msg)

                    for tc in assistant_msg.tool_calls:
                        args = json.loads(tc.function.arguments)
                        result_str = dispatch_tool_call(tc.function.name, args, user_email)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": result_str,
                        })



                else:
                    reply = choice.message.content or "Done."
                    save_message(conv, "assistant", reply)
                    return reply



        except BadRequestError as e:
            # Model likely does not support tool calling — fall back
            if "tool" in str(e).lower() or "function" in str(e).lower():
                return _run_agent_fallback(messages, user_email, conv)
            raise



    else:
        return _run_agent_fallback(messages, user_email, conv)



    fallback = "I couldn't complete that request. Please try again."
    save_message(conv, "assistant", fallback)
    return fallback
