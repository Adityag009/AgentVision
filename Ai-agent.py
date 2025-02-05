from phi.agent import Agent, RunResponse
from phi.model.groq import Groq
from dotenv import load_dotenv
from phi.tools.yfinance import YFinanceTools
from phi.tools.duckduckgo import DuckDuckGo

load_dotenv()

# agent= Agent(
#     model=Groq(id="llama-3.3-70b-versatile"),
#     tools=[YFinanceTools(stock_price=True,analyst_recommendations=True,stock_fundamentals=True)],
#     description="You are an investment analyst that researches stock prices, analyst recommendations, and stock fundamentals.",
#     show_tool_calls=True,
#     markdown=True,
#     instruction=["Use tables to display data."]
#
# )
#
# agent.print_response("Summarize and Compare analyst recommendation and fundamentals for TCS and Infosys")

web_agent = Agent(
    name="Web Agent",
    role="Search the web for information",
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[DuckDuckGo()],
    instructions=["Always include sources"],
    show_tool_calls=True,
    markdown=True,
)

finance_agent = Agent(
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[YFinanceTools(stock_price=True, analyst_recommendations=True, stock_fundamentals=True)],
    description="You are an investment analyst that researches stock prices, analyst recommendations, and stock fundamentals.",
    show_tool_calls=True,
    markdown=True,
    instruction=["Use tables to display data."]
)


agent_team = Agent(
    team=[web_agent, finance_agent],
    instructions=["Always include sources", "Use tables to display data"],
    show_tool_calls=True,
    markdown=True,
)

agent_team.print_response("Summarize and Compare analyst recommendation and fundamentals for TCS and Infosys",stream=True)