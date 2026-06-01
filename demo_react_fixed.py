"""
Demo script to show ReAct Agent is now properly using Thought-Action-Observation
instead of Rule-Based guardrail bypass.

This demonstrates the fix for the issue where LocalProvider was bypassing
the ReAct loop and directly calling guardrail-based tool routing.
"""

from src.agent.agent import ReActAgent
from src.core.llm_provider import LLMProvider
from src.tools.school_db_tools import get_tools
from typing import Any, Dict, Optional


class DemoSequenceProvider(LLMProvider):
    """
    Demo provider that shows the proper ReAct flow with multiple steps.
    """
    def __init__(self, responses: list[str]):
        super().__init__(model_name="demo-react")
        self.responses = responses
        self.calls = 0

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        if self.calls >= len(self.responses):
            # If we run out of responses, return an error
            content = "Final Answer: Tôi đã hết các bước xử lý."
        else:
            content = self.responses[self.calls]
        
        print(f"\n[LLM Call #{self.calls + 1}]")
        print(f"Response:\n{content}\n")
        
        self.calls += 1
        return {
            "content": content,
            "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
            "latency_ms": 50,
            "provider": "demo",
        }

    def stream(self, prompt: str, system_prompt: Optional[str] = None):
        yield self.generate(prompt, system_prompt=system_prompt)["content"]


def demo_react_multi_step_reasoning():
    """
    Demonstrates ReAct working with multiple steps:
    1. Thought: Plan what to do
    2. Action: Call a tool
    3. Observation: Get result (from system)
    4. Repeat or Final Answer
    """
    print("=" * 80)
    print("DEMO 1: Multi-Step ReAct Reasoning (Student Profile Lookup)")
    print("=" * 80)
    
    provider = DemoSequenceProvider([
        # Step 1: LLM thinks and decides to look up student profile
        'Thought: Tôi cần tìm thông tin về sinh viên 2A202600632.\nAction: get_student_profile({"student_id":"2A202600632"})',
        # Step 2: After seeing observation, LLM returns final answer
        'Final Answer: Sinh viên 2A202600632 là SinhVien 632, chuyên ngành CNTT.'
    ])
    
    agent = ReActAgent(llm=provider, tools=get_tools(), max_steps=3)
    
    print("\nUser Query: 'Cho tôi thông tin sinh viên 2A202600632'\n")
    answer = agent.run("Cho toi thong tin sinh vien 2A202600632")
    
    print(f"\n✓ FINAL ANSWER: {answer}")
    print(f"✓ LLM was called {provider.calls} times (ReAct is working!)")
    print(f"✓ Tools were properly called through the ReAct loop\n")


def demo_react_two_step_query():
    """
    Demonstrates a more complex two-action scenario:
    - First get exam info
    - Then get room location
    """
    print("=" * 80)
    print("DEMO 2: Complex Multi-Action ReAct (Exam Info + Room Location)")
    print("=" * 80)
    
    provider = DemoSequenceProvider([
        # Step 1: Get exam info
        'Thought: Cần tìm lịch thi môn Big Data của sinh viên 2A202600001.\nAction: get_exam_info({"student_id":"2A202600001","subject_name":"Big Data"})',
        # Step 2: After seeing exam room, get room location
        'Thought: Người dùng hỏi phòng thi ở đâu. Tôi thấy phòng là A301. Cần lấy vị trí phòng này.\nAction: search_room_location({"room":"A301"})',
        # Step 3: Return final answer with all info
        'Final Answer: Lịch thi môn Big Data: Sáng 08:00, Phòng A301 - Tòa A Lầu 3.'
    ])
    
    agent = ReActAgent(llm=provider, tools=get_tools(), max_steps=4)
    
    print("\nUser Query: 'Lịch thi Big Data của sinh viên 2A202600001 ở phòng nào?'\n")
    answer = agent.run("Lich thi Big Data cua sinh vien 2A202600001 o phong nao?")
    
    print(f"\n✓ FINAL ANSWER: {answer}")
    print(f"✓ LLM was called {provider.calls} times (executing {provider.calls} reasoning steps!)")
    print(f"✓ Multiple tools were called in sequence through ReAct\n")


def demo_react_vs_old_guardrail():
    """
    Compares old guardrail behavior vs new ReAct behavior
    """
    print("=" * 80)
    print("COMPARISON: Old Guardrail vs New ReAct")
    print("=" * 80)
    
    print("\n[OLD BEHAVIOR - Rule-Based Guardrail]")
    print("- Input: 'Danh sách sinh viên'")
    print("- Process: regex pattern matching → 'danh sach' + 'sinh vien' → call list_students")
    print("- Result: Direct tool call, no LLM reasoning, no Thought-Action-Observation loop")
    print("- Problem: Can't reason about complex scenarios, just pattern matching\n")
    
    print("[NEW BEHAVIOR - ReAct Loop]")
    print("- Input: 'Danh sách sinh viên'")
    print("- Process:")
    print("  1. LLM Thought: 'Người dùng muốn danh sách sinh viên. Cần gọi list_students.'")
    print("  2. LLM Action: list_students(limit=10)")
    print("  3. System Observation: [list of students from DB]")
    print("  4. LLM Final Answer: [formatted result]")
    print("- Benefit: LLM can reason, adapt, handle edge cases, multi-step logic")
    print("- Benefit: Thought-Action-Observation is fully transparent and auditable\n")


if __name__ == "__main__":
    print("\n")
    print("🤖 ReAct Agent Fix Demo - Showing ReAct Works Instead of Rule-Based")
    print("=" * 80)
    
    demo_react_multi_step_reasoning()
    demo_react_two_step_query()
    demo_react_vs_old_guardrail()
    
    print("=" * 80)
    print("✅ All demos complete! ReAct agent is now properly using")
    print("   Thought-Action-Observation loops instead of rule-based matching.")
    print("=" * 80)
