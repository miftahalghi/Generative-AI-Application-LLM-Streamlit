import os
from bot.agent import build_agent

agent = build_agent()
config = {"configurable": {"thread_id": "test_1"}}

print("=== Turn 1 ===")
res1 = agent.invoke({"messages": [("user", "hi, my name is Budi")]}, config)
print(res1["messages"][-1].content)

print("=== Turn 2 ===")
res2 = agent.invoke({"messages": [("user", "what is my name?")]}, config)
print(res2["messages"][-1].content)

print("=== Turn 3 (Tool) ===")
res3 = agent.invoke({"messages": [("user", "multiply 10 and 5")]}, config)
for msg in res3["messages"]:
    if msg.type == "tool":
        print("TOOL CALLED:", msg.name)
print("FINAL:", res3["messages"][-1].content)
