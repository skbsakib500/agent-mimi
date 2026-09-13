"""Agent Mimi - automation rule definitions."""
from dataclasses import dataclass

STUDY_TARGET_7D = 7.0
GOAL_LOW_PROGRESS = 25
MISSION_LOW_PROGRESS = 25
PHONE_WARNING = 240
SLEEP_WARNING = 360


@dataclass(frozen=True)
class Rule:
    code: str
    severity: str
    title: str
    message: str
    module: str


def study_low(hours):
    if hours < STUDY_TARGET_7D:
        return Rule("STUDY_LOW", "warning",
                    "Study target below weekly goal",
                    f"Only {hours:.1f}h in last 7 days; target {STUDY_TARGET_7D:.1f}h.",
                    "study")


def goal_low(avg):
    if avg < GOAL_LOW_PROGRESS:
        return Rule("GOAL_LOW", "warning",
                    "Goal progress is low",
                    f"Average active goal progress {avg:.1f}%.",
                    "goals")


def mission_low(avg):
    if avg < MISSION_LOW_PROGRESS:
        return Rule("MISSION_LOW", "warning",
                    "Mission progress is low",
                    f"Average mission progress {avg:.1f}%.",
                    "missions")


def task_overdue(n):
    if n:
        return Rule("TASK_OVERDUE", "critical",
                    "Overdue tasks detected",
                    f"{n} pending task(s) past due date.",
                    "tasks")


def task_due_soon(n):
    if n:
        return Rule("TASK_DUE_SOON", "warning",
                    "Tasks due soon",
                    f"{n} task(s) due within 1 day.",
                    "tasks")


def finance_negative(balance):
    if balance < 0:
        return Rule("FINANCE_NEG", "critical",
                    "Cash flow negative",
                    f"Recorded income minus expenses {balance:,.2f}.",
                    "finance")


def sleep_low(avg_min):
    if avg_min and avg_min < SLEEP_WARNING:
        return Rule("SLEEP_LOW", "warning",
                    "Average sleep is low",
                    f"Average {avg_min/60:.1f}h per night.",
                    "sleep")
