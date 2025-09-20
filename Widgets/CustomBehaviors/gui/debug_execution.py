import os
from collections import deque
from datetime import datetime

from Py4GWCoreLib import ImGui, PyImGui
from Py4GWCoreLib.enums_src.Texture_enums import get_texture_for_skill
from Widgets.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager
from Widgets.CustomBehaviors.primitives.skills.utility_skill_execution_history import UtilitySkillExecutionHistory

shared_data = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
script_directory = os.path.dirname(os.path.abspath(__file__))

@staticmethod
def render():
    
    PyImGui.text(f"History (newest on top) : ")
    if PyImGui.begin_child("x", size=(400, 600),border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar):

        behavior = CustomBehaviorLoader().custom_combat_behavior
        if behavior is None: return
        results:deque[UtilitySkillExecutionHistory] = behavior.skill_execution_history

        # simple table with skill picture and name
        if PyImGui.begin_table("history_skills", 2, int(PyImGui.TableFlags.SizingStretchProp)):
            PyImGui.table_setup_column("Icon")
            PyImGui.table_setup_column("Name")
            for result in reversed(results):

                texture_file = get_texture_for_skill(result.skill.custom_skill.skill_id)
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                ImGui.DrawTexture(texture_file, 30, 30)
                PyImGui.table_next_column()
                time_started_at = datetime.fromtimestamp(result.started_at)
                time_started_at_formatted = f"{time_started_at:%H:%M:%S}:{int(time_started_at.microsecond/1000):03d}"
                PyImGui.text(f"started:{time_started_at_formatted}")
                PyImGui.same_line(0,0)
                PyImGui.text(f"| {result.skill.custom_skill.skill_name}")
                if result.ended_at is not None:
                    time_executed_at = datetime.fromtimestamp(result.ended_at)
                    time_executed_at_formatted = f"{time_executed_at:%H:%M:%S}:{int(time_executed_at.microsecond/1000):03d}"
                    PyImGui.text(f"ended:{time_executed_at_formatted}")
                    PyImGui.same_line(0,0)
                res_val = getattr(result, "result", None)
                enum_text = res_val.name if res_val is not None else "None"
                PyImGui.text(f"| {enum_text}")
                PyImGui.separator()
            PyImGui.end_table()
           


        PyImGui.end_child()
