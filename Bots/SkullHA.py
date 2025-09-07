from time import sleep
from Py4GWCoreLib import *
import random
import json
import re

module_name = "HA Bot"
henchmen_ids = [11,12,13,14,6,8,7]

#Map ID's
heroes_ascent = 330
underworld = 84
fetid_river = 593
burial_mounds = 80
unholy_temples = 81
gtob = 248

#Chat Strings
chat_won_zaishen = r"Your team completed the mission in \d+ minutes? and \d+ seconds."
chat_won_map = "You have gained 200 faction with Balthazar for winning!"
chat_won_burial = "You gain 3 Fame for this win." 
chat_won_map_double_fame = "You have gained 400 faction with Balthazar for winning!"

#We use this filter later on to get the amount of wins from chat system message.
#Each new run starts after winning Zaishens
def filter_chat_from_last_zaishen_win(chat, pattern):
    regex = re.compile(pattern)
    
    for i in reversed(range(len(chat))):
        if regex.match(chat[i]):
            return chat[i:]
    
    return []

#Used to count how many wins since we last beat zaishen
#Requires filtered chat from above fn  
def get_wins_in_run(filtered_chat, win_message):
    return sum(1 for message in filtered_chat if message == win_message) 

#Quest Id's
ha_quest_id = 1118 #1110
ha_take_dialog_id = 8674817 #8672769
ha_receive_dialog_id = 8674823 #8674819 #8672775

#Key Map Points
underworld_below_bridge_xy = (67, -3341)
burial_red_spawn_xy = (-6596, 2311)

class BotVariables:
    state: str = "Sleeping"
    action_timer = Timer()
    action_check = 0
    restart_fsm = False 
    starting_win_streak = 0
    lock_timer = False
    sent_first_dialog = False
    sent_second_dialog = False
    sent_map_travel = False
    team_color = ""
    ha_quest_button_state = False
    win_streak = 6
    has_interacted = False
    max_tries = 0
    interaction_stage = 0
    wins_in_run = 0
    has_resigned = False
    chat_request_timer = Timer()
    has_requested_chat = False
    latest_raw_chat = []
    stop_buying_keys_button_state = False
    wait_for_fame_button_state = False
    
class FSMVariables:
    fsm        = FSM('HA bot')
    move       = Routines.Movement.FollowXY()
    exact_move = Routines.Movement.FollowXY(tolerance=5)
    do_setup   = True

class Routines:
    @staticmethod
    def WinsCounter(current_map_id, wait_for_fame=False): # checks for win messages in chat while running, adds to state.
        
        if Map.IsMapLoading() or not Map.IsMapReady():
            return
        
        if not BotVariables.chat_request_timer.IsRunning():
            Py4GW.Console.Log("Routine", "Starting Chat Request Timer")
            BotVariables.chat_request_timer.Start()
        
        if BotVariables.chat_request_timer.HasElapsed(10000) and not BotVariables.has_requested_chat:
                Player.RequestChatHistory()
                Py4GW.Console.Log("Routine", "Requested Chat History")
                BotVariables.has_requested_chat = True
           
        if Player.IsChatHistoryReady() and BotVariables.has_requested_chat:
                chat = filter_chat_from_last_zaishen_win(Player.GetChatHistory(), chat_won_zaishen)
                if wait_for_fame:
                    wins_in_chat = get_wins_in_run(chat, chat_won_burial) # is always 0 in current run till burial win msg appears
                    BotVariables.wins_in_run = 0 # resetting since we parse fame msg instead of win msg now, otherwise conditional would never work
                    if wins_in_chat > BotVariables.wins_in_run:
                        BotVariables.win_streak += 1
                else:
                    wins_in_chat = get_wins_in_run(chat, chat_won_map)
                    
                if wins_in_chat > BotVariables.wins_in_run:
                    BotVariables.wins_in_run = wins_in_chat
                    BotVariables.win_streak += 1
                    Py4GW.Console.Log("win detected",  f"won in {current_map_id}, current win streak {BotVariables.win_streak}, wins this run {BotVariables.wins_in_run}")
                BotVariables.has_requested_chat = False
                BotVariables.chat_request_timer.Stop()
                BotVariables.chat_request_timer.Reset()

    @staticmethod
    def PracticeRotation():
        if Map.IsMapLoading() or not Map.IsMapReady():
            return
            
        my_id = Player.GetAgentID()
        my_energy = Combat.GetMyEnergy()
       
        #Sepll ID's for important  spells, Does not include Panic
        rupt_targets = [1118, 2866, 280, 189, 3021, 1083, 167, 196, 282]
        #Longer casts for safe mana regen via Power Drain
        safe_rupt_targets = [189, 3021, 1083, 167, 196, 282]
       
      #  Py4GW.Console.Log("Routine", "Practicing Rotation")
      
        alive_enemies = Combat.GetAliveEnemies()
        in_range_enemies =  Combat.GetSpellRangeEnemies(alive_enemies)
        
        if not alive_enemies:
            return

        if in_range_enemies:
            best_target = AgentArray.Routines.DetectLargestAgentCluster(in_range_enemies, 100)
        else:
            best_target = AgentArray.Routines.DetectLargestAgentCluster(alive_enemies, 100)

        target = best_target
        
        if BotVariables.action_timer.IsRunning():
            return
        
        #Main Attack Rotation + Rupts
        if target and target != 0 and Agent.IsAlive(target) and not Map.IsMapLoading() and AgentArray.Filter.ByDistance(alive_enemies, Player.GetXY(), Range.Spellcast.value - 200) and Map.IsMapReady():
            if my_energy > 10 and Combat.IsRecharged(2) and SkillBar.GetCasting() == 0:
                if my_energy > 15 and Combat.IsRecharged(2):
                    Combat.CastSpell(1, target)
                Player.Interact(target)    
                Combat.CastSpell(2, target)
                
            if not Combat.IsRecharged(2) and my_energy > 15 and SkillBar.GetCasting() == 0 and Map.GetMapID():
                Combat.CastSpell(4, target)
                
            if not Combat.IsRecharged(2) and my_energy > 15 and not Combat.IsRecharged(4) and SkillBar.GetCasting() == 0:
                Combat.CastSpell(3, target)

            if not Combat.IsRecharged(2) and not Combat.IsRecharged(4) and SkillBar.GetCasting() == 0:
                Combat.CastSpell(5, target)

            # if not Combat.IsRecharged(2) and not Combat.IsRecharged(5) and SkillBar.GetCasting() == 0:
            #     Combat.CastSpell(6, target) 

            for agent_id in in_range_enemies:
                if Agent.IsCasting(agent_id) and (not Agent.IsCasting(my_id) and not Agent.IsKnockedDown(my_id)):
                    
                    if Agent.GetCastingSkill(agent_id) in (52, 1095) and Combat.IsRecharged(8): #Panic = 52, Star Burst = 1095
                        Combat.CastSpell(8, agent_id)
                        
                    if Agent.GetCastingSkill(agent_id) in rupt_targets and Combat.GetMyEnergy() > 20 and Combat.IsRecharged(7) and SkillBar.GetCasting() == 0:
                        Combat.CastSpell(7, agent_id)
                        
                    if Agent.GetCastingSkill(agent_id) in (77, 202) and Combat.GetMyEnergy() > 5 and Combat.IsRecharged(6) and SkillBar.GetCasting() == 0:
                        Combat.CastSpell(6, agent_id) # 77 = Chaos Storm, 202 = Glyph of Sacrifice, counters enemy bots with meteor shower
                        
                    elif Agent.GetCastingSkill(agent_id) in safe_rupt_targets and Combat.GetMyEnergy() < 20 and Combat.IsRecharged(7) and SkillBar.GetCasting() == 0:
                        Combat.CastSpell(7, agent_id)
                        
        else:
            Combat.MoveToXYWithRandomness(Agent.GetXY(best_target)[0], Agent.GetXY(best_target)[1], 50) 
            
    @staticmethod
    def TravelToHA():    
        if Map.IsMapLoading() or not Map.IsMapReady():
            return
        
        if not Party.IsPartyLoaded():
            return
        
        if Map.IsOutpost() and Map.GetMapID() != heroes_ascent:
            Map.Travel(heroes_ascent)
        
        if Map.GetMapID() == heroes_ascent and not Map.IsExplorable() and not Map.IsMapLoading() and Map.IsMapReady():
            Py4GW.Console.Log("Routine", "Already in Heroes Ascent")
            BotVariables.action_timer.Stop()
            BotVariables.action_timer.Reset()
            next_step = FSMVariables.fsm.get_next_step_name()
            if next_step:
                FSMVariables.fsm.jump_to_state_by_name(next_step)
            return

    @staticmethod
    def WaitForResign():
        if Map.IsMapLoading() or not Map.IsMapReady():
            return
        
        if not Party.IsPartyLoaded():
            return
        
        if Map.IsExplorable() and Map.GetMapID() != heroes_ascent:
            if Map.GetInstanceUptime() > 305000 and not BotVariables.has_resigned:
                Player.SendChatCommand("resign")
                BotVariables.has_resigned = True
        
        if not Map.IsExplorable() and not Map.IsMapLoading() and Map.IsMapReady():
            Py4GW.Console.Log("Routine", "Returned safely to HA")
            next_step = FSMVariables.fsm.get_next_step_name()
            if next_step:
                FSMVariables.fsm.jump_to_state_by_name(next_step)
            return

    @staticmethod
    def TravelToGTOB():
        
        if Map.IsMapLoading() or not Map.IsMapReady() or not Party.IsPartyLoaded() or Map.IsExplorable():
            return
        
        if BotVariables.ha_quest_button_state == False or Quest.GetActiveQuest() == ha_quest_id and BotVariables.win_streak < 6:
            next_step = FSMVariables.fsm.get_next_step_name()
            if next_step:
                FSMVariables.fsm.jump_to_state_by_name(next_step)
            return
        
        if Quest.GetActiveQuest() == ha_quest_id and BotVariables.win_streak >= 6 and not Map.IsMapLoading() and Map.IsMapReady() and not Map.GetMapID() == gtob:
            BotVariables.action_timer.Stop()
            Map.Travel(gtob)
            return
        
        if Quest.GetActiveQuest() == 0 and not Map.IsMapLoading() and Map.IsMapReady() and not Map.GetMapID() == gtob:
            BotVariables.action_timer.Stop()
            Map.Travel(gtob)
            return
        
        if Map.GetMapID() == gtob and not Map.IsMapLoading() and Map.IsMapReady():
            Combat.MoveToXYWithRandomness(-5358, -5463, 5)
            return
             
    @staticmethod
    def GetQuest():
        if Map.IsMapLoading() or not Map.IsMapReady():
            return
        
        if Map.GetMapID() != gtob:
            next_step = FSMVariables.fsm.get_next_step_name()
            if next_step:
                FSMVariables.fsm.jump_to_state_by_name(next_step)
            return
        
        if Quest.GetActiveQuest() == ha_quest_id and BotVariables.interaction_stage == 0:
            BotVariables.action_timer.Stop()
            next_step = FSMVariables.fsm.get_next_step_name()
            if next_step:
                FSMVariables.fsm.jump_to_state_by_name(next_step)
            return
           
        if Map.IsMapLoading() or not Map.IsMapReady() or not Party.IsPartyLoaded() or Map.IsExplorable():
            return
        
        if BotVariables.ha_quest_button_state == False:
            next_step = FSMVariables.fsm.get_next_step_name()
            if next_step:
                FSMVariables.fsm.jump_to_state_by_name(next_step)
            return
        
        if Map.GetMapID() == gtob and Quest.GetActiveQuest() == 0 and not BotVariables.action_timer.IsRunning() and not BotVariables.has_interacted:
            BotVariables.action_timer.Start()
            Combat.MoveToXYWithRandomness(-5217, -5416, 5)
            
        if not Agent.IsMoving(Player.GetAgentID()) and BotVariables.action_timer.IsRunning() and BotVariables.action_timer.HasElapsed(5000):
            npc_array = AgentArray.GetNPCMinipetArray()
            closest_npc = AgentArray.Filter.ByDistance(npc_array, [-5217, -5416], 200)
            if not BotVariables.has_interacted: 
                Player.Interact(closest_npc[0])
                BotVariables.action_timer.Stop()
                BotVariables.action_timer.Start()
                BotVariables.has_interacted = True
                
            if BotVariables.has_interacted and BotVariables.action_timer.HasElapsed(1000) and BotVariables.interaction_stage == 0:
                Py4GW.Console.Log("dialog", "sent dialog")
                Player.SendDialog(ha_take_dialog_id)
                BotVariables.win_streak = 0
                BotVariables.interaction_stage = 1
                BotVariables.action_timer.Stop()
                BotVariables.action_timer.Start()
                BotVariables.interaction_stage = 0
                BotVariables.has_interacted = False
                BotVariables.restart_fsm = True
                
            if BotVariables.has_interacted and BotVariables.action_timer.HasElapsed(2000) and BotVariables.interaction_stage == 1:
                BotVariables.has_interacted = False
                BotVariables.interaction_stage = 0
                BotVariables.action_timer.Stop()
                BotVariables.restart_fsm = True

    @staticmethod
    def CompleteQuest():
        if Map.IsMapLoading() or not Map.IsMapReady():
            return

        if Map.GetMapID() != gtob:
            next_step = FSMVariables.fsm.get_next_step_name()
            if next_step:
                FSMVariables.fsm.jump_to_state_by_name(next_step)
            return

        if BotVariables.win_streak < 6 or Quest.GetActiveQuest() != ha_quest_id and BotVariables.interaction_stage != 3:
            return

        if BotVariables.interaction_stage == 0 and Map.GetMapID() == gtob and Quest.GetActiveQuest() == ha_quest_id and BotVariables.win_streak >= 6 and not BotVariables.action_timer.IsRunning() and not BotVariables.has_interacted:            
            BotVariables.action_timer.Start()
            Combat.MoveToXYWithRandomness(-5157, -5528, 5)
            BotVariables.interaction_stage = 1
       
        if BotVariables.interaction_stage == 1 and not Agent.IsMoving(Player.GetAgentID()) and BotVariables.action_timer.HasElapsed(8000):
            npc_array = AgentArray.GetNPCMinipetArray()
            closest_npc = AgentArray.Filter.ByDistance(npc_array, [-5212, -5540], 200)
            if closest_npc:
                Player.Interact(closest_npc[0])
                BotVariables.action_timer.Stop()
                BotVariables.action_timer.Start()
                BotVariables.has_interacted = True
                BotVariables.interaction_stage = 2

        if BotVariables.interaction_stage == 2 and BotVariables.action_timer.HasElapsed(1000):
            Py4GW.Console.Log("dialog", "sent dialog")
            Player.SendDialog(ha_receive_dialog_id)
            BotVariables.interaction_stage = 3
            BotVariables.action_timer.Stop()
            BotVariables.action_timer.Start()
            BotVariables.has_interacted = False
            BotVariables.win_streak = 0
            BotVariables.interaction_stage = 0
            BotVariables.restart_fsm = True
            
        if BotVariables.interaction_stage == 3 and BotVariables.action_timer.HasElapsed(2000):
            Py4GW.Console.Log("w ", "xd")
            BotVariables.restart_fsm = True
            BotVariables.has_interacted = False
            BotVariables.win_streak = 0
            BotVariables.action_timer.Stop()
            BotVariables.interaction_stage = 0
            
    @staticmethod
    def AddHenchmen():
        if Map.GetMapID() == heroes_ascent and not Map.IsExplorable() and not Map.IsMapLoading() and Map.IsMapReady():
                Py4GW.Console.Log("Routine", "Adding Henchmen")
                if Party.GetPartySize() < 8:
                    for id in henchmen_ids:
                        Party.Henchmen.AddHenchman(id)
                        #Py4GW.Console.Log("Routine", "Added Henchman " + str(id))
                    else:
                        return  
                
    @staticmethod
    def SendDialogs():
        if not Map.GetMapID() == heroes_ascent and not Map.IsExplorable() and not Map.IsMapLoading() and Map.IsMapReady():
            next_step = FSMVariables.fsm.get_next_step_name()
            if next_step:
                FSMVariables.fsm.jump_to_state_by_name(next_step)
            return

        if BotVariables.stop_buying_keys_button_state:
            next_step = FSMVariables.fsm.get_next_step_name()
            if next_step:
                FSMVariables.fsm.jump_to_state_by_name(next_step)
            return

        if BotVariables.interaction_stage > 3:
            BotVariables.interaction_stage = 0
            BotVariables.action_timer.Stop()
            next_step = FSMVariables.fsm.get_next_step_name()
            if next_step:
                FSMVariables.fsm.jump_to_state_by_name(next_step)
            return

        if Player.GetBalthazarData()[0] < 5000:
            next_step = FSMVariables.fsm.get_next_step_name()
            if next_step:
                FSMVariables.fsm.jump_to_state_by_name(next_step)
            return
        
        if not BotVariables.action_timer.IsRunning():
            BotVariables.action_timer.Start()
        
        if BotVariables.action_timer.HasElapsed(1000) and not BotVariables.sent_first_dialog:
            Player.SendDialog(135)
            #Py4GW.Console.Log("Routine", "Sent Dialog 135")
            BotVariables.sent_first_dialog = True
            
        if BotVariables.action_timer.HasElapsed(2000) and BotVariables.sent_first_dialog:
            #Py4GW.Console.Log("Routine", "Sent Dialog 136")
            Player.SendDialog(136)
            BotVariables.interaction_stage += 1
            BotVariables.sent_first_dialog = False
            BotVariables.action_timer.Stop()     
            
    @staticmethod
    def BuyZkeys():
        if not Map.GetMapID() == heroes_ascent and not Map.IsExplorable() and not Map.IsMapLoading() and Map.IsMapReady():
            next_step = FSMVariables.fsm.get_next_step_name()
            if next_step:
                FSMVariables.fsm.jump_to_state_by_name(next_step)
            return

        if BotVariables.stop_buying_keys_button_state:
            next_step = FSMVariables.fsm.get_next_step_name()
            if next_step:
                FSMVariables.fsm.jump_to_state_by_name(next_step)
            return
        
        if Player.GetBalthazarData()[0] < 5000:
            Py4GW.Console.Log("Routine", "Balthazar points under 5k, Not buying Zkeys")
            next_step = FSMVariables.fsm.get_next_step_name()
            if next_step:
                FSMVariables.fsm.jump_to_state_by_name(next_step)
            return
        
        if Player.GetBalthazarData()[0] >= 5000 and not Map.IsMapLoading() and Map.IsMapReady():
            npcs_only = AgentArray.Filter.ByCondition(AgentArray.GetNPCMinipetArray(), lambda agent_id: Agent.IsNPC(agent_id))
            tolkano_location = AgentArray.Filter.ByDistance(npcs_only, (1226, -5044), 100)
        
            if tolkano_location:
                Player.Interact(tolkano_location[0])
                
        else:
            Py4GW.Console.Log("Routine", "Tolkano not found, moving to middle of map and restarting")
            Combat.MoveToXYWithRandomness(3500, -3500, 50)
            BotVariables.restart_fsm = True
            return
        
                             
    @staticmethod
    def EnterMission():
        if Agent.IsHexed(Player.GetAgentID()):
            return
        
        if Map.IsMapLoading() and not Map.IsMapReady():
            return
        
            
        if not Map.GetMapID() == heroes_ascent:
            Py4GW.Console.Log("Routine", "Done with HA Mission")
            next_step = FSMVariables.fsm.get_next_step_name()
            if next_step:
                FSMVariables.fsm.jump_to_state_by_name(next_step)
            return 
        
        if Map.GetMapID() == heroes_ascent and not Map.IsExplorable() and not Map.IsMapLoading() and Map.IsMapReady() and Party.GetPartySize() >= 8:
            Py4GW.Console.Log("Routine", "Entering HA Mission")
            BotVariables.wins_in_run = 0
            BotVariables.has_resigned = False
            BotVariables.lock_timer = False
            BotVariables.has_requested_chat = False
            BotVariables.chat_request_timer.Stop()
            BotVariables.chat_request_timer.Reset()
            BotVariables.action_timer.Stop()
            BotVariables.interaction_stage = 0
            Map.EnterChallenge()
            
    @staticmethod
    def Zaishen():
        if Map.IsMapLoading() or not Map.IsMapReady():
            return
        
        if not Map.GetMapID() == heroes_ascent and not Map.IsMapLoading() and Map.IsMapReady():
            Py4GW.Console.Log("Routine", "Done with Zaishens")
            next_step = FSMVariables.fsm.get_next_step_name()
            if next_step:
                FSMVariables.fsm.jump_to_state_by_name(next_step)
        
        if Map.GetMapID() == heroes_ascent and Map.IsExplorable():
            Routines.PracticeRotation()
            return
  
    @staticmethod
    def Underworld():
        if Map.IsMapLoading() or not Map.IsMapReady():
            return
        
        if not Map.GetMapID() == underworld and not Map.IsMapLoading() and Map.IsMapReady():
            if Map.GetMapID() == heroes_ascent and not Map.IsExplorable():
                #Py4GW.Console.Log("Routine", "Defeated at Underworld, We go again")
                BotVariables.restart_fsm = True  
                return
            
            else:
                Py4GW.Console.Log("Routine", "Done with Underworld")
                next_step = FSMVariables.fsm.get_next_step_name()
                if next_step:
                    FSMVariables.fsm.jump_to_state_by_name(next_step)
                return
        
        if Map.GetMapID() == underworld and not Map.IsMapLoading() and Map.IsMapReady():
            if Map.IsInCinematic():
                Map.SkipCinematic()
                return
            
            if Map.GetInstanceUptime() < 50000:
                return
            
            Routines.WinsCounter(Map.GetMapName(Map.GetMapID()))
            
            if Map.GetInstanceUptime() > 51000 and not AgentArray.GetEnemyArray() and not Combat.AmIMoving() and Map.IsMapReady() and not Map.IsMapLoading():
                #Py4GW.Console.Log("Routine", "Moving to Location" + str(Map.GetInstanceUptime()))
                Combat.MoveToXYWithRandomness(*underworld_below_bridge_xy, 50)
                
            if Combat.GetAliveEnemies():
                Routines.PracticeRotation()

    @staticmethod
    def Fetid_River():
        if Map.IsMapLoading() or not Map.IsMapReady() or not Party.IsPartyLoaded():
            return
        
        if not Map.GetMapID() == fetid_river and not Map.IsMapLoading() and Map.IsMapReady():
            if Map.GetMapID() == heroes_ascent and not Map.IsExplorable() and not Map.IsMapLoading() and Map.IsMapReady():
                Py4GW.Console.Log("Routine", "Defeated at Fetid River, We go again")
                BotVariables.restart_fsm = True   
                return
            
            else:
                Py4GW.Console.Log("Routine", "Done with Fetid")
                next_step = FSMVariables.fsm.get_next_step_name()
                if next_step:
                    FSMVariables.fsm.jump_to_state_by_name(next_step)
                return
        
        if Map.GetMapID() == fetid_river and not Map.IsMapLoading() and Map.IsMapReady():
            if Map.IsInCinematic():
                Map.SkipCinematic()
                return
            
            if Map.GetInstanceUptime() < 60000:
                return
            
            Routines.WinsCounter(Map.GetMapName(Map.GetMapID()))
            
            if Combat.GetAliveEnemies():
                Routines.PracticeRotation()
    
    @staticmethod
    def Burial_Mounds():    
        if Map.IsMapLoading() or not Map.IsMapReady():
            return
        
        if Map.GetMapID() not in [burial_mounds, heroes_ascent]:
            BotVariables.restart_fsm = True
            return
        
        if not Map.GetMapID() == burial_mounds and not Map.IsMapLoading() and Map.IsMapReady():
            if Map.GetMapID() == heroes_ascent and not Map.IsExplorable() and not Map.IsMapLoading() and Map.IsMapReady():
                #Py4GW.Console.Log("Routine", "Defeated at Burial Mounds, We go again")
                BotVariables.restart_fsm = True 
                return
        
        if Map.GetMapID() == burial_mounds and not Map.IsMapLoading() and Map.IsMapReady():
            if BotVariables.wait_for_fame_button_state:
                Routines.WinsCounter(Map.GetMapName(Map.GetMapID()), wait_for_fame=True)
            else:
                Routines.WinsCounter(Map.GetMapName(Map.GetMapID()))
            
            if Map.IsInCinematic():
                Map.SkipCinematic()
                BotVariables.starting_win_streak = BotVariables.win_streak
                BotVariables.team_color = Combat.GetTeamColorBySpawnPoint(burial_red_spawn_xy, "red", Player.GetXY()) #does nothing but scared to remove it
                #Py4GW.Console.Log("Burial", f"current team color {BotVariables.team_color}")
                return
            
            if Map.GetInstanceUptime() < 59000:
                return
            
            
            if Combat.GetAliveEnemies():
                Routines.PracticeRotation()
            
            if BotVariables.win_streak > BotVariables.starting_win_streak and not Map.IsMapLoading() and Map.IsMapReady(): 
                if not BotVariables.action_timer.IsRunning() and not Map.IsMapLoading() and Map.IsMapReady():
                    Py4GW.Console.Log("Routine", "Won at Burial, restarting run")
                    Map.Travel(heroes_ascent) 
                    BotVariables.action_timer.Stop()
                    BotVariables.action_timer.Reset()
                    BotVariables.action_timer.Start()
                    
                if BotVariables.action_timer.IsRunning() and not Map.IsMapLoading() and Map.IsMapReady() and BotVariables.wait_for_fame_button_state:
                    if BotVariables.action_timer.HasElapsed(1500):
                        Keystroke.PressAndRelease(Key.Y.value) 
              
                
               
                
           

#FSMVariables.fsm.AddState(name="Testing Damage Rotation", execute_fn=lambda: Routines.PracticeRotation(), exit_condition=lambda: Map.GetMapID() == heroes_ascent and not Map.IsMapLoading() and Map.IsMapReady(), transition_delay_ms=10000, run_once=False)      
FSMVariables.fsm.AddState(name="Waiting to Resign", execute_fn=lambda: Routines.WaitForResign(), exit_condition=lambda: Map.GetMapID() == heroes_ascent and not Map.IsMapLoading() and Map.IsMapReady(), transition_delay_ms=5000, run_once=False) 
FSMVariables.fsm.AddState(name="Travelling to HA", execute_fn=lambda: Routines.TravelToHA(), exit_condition=lambda: Map.GetMapID() == heroes_ascent and not Map.IsMapLoading() and Map.IsMapReady(), transition_delay_ms=5000, run_once=True)
FSMVariables.fsm.AddState(name="Checking Zaishen Quest State", execute_fn=lambda: Routines.TravelToGTOB(), exit_condition=lambda: Map.GetMapID() == gtob and not Map.IsMapLoading() and Map.IsMapReady(), transition_delay_ms=2000, run_once=True)
FSMVariables.fsm.AddState(name="Getting Quest", execute_fn=lambda: Routines.GetQuest(), exit_condition=lambda: Map.GetMapID() == gtob and not Map.IsMapLoading() and Map.IsMapReady() and Quest.GetActiveQuest() == ha_quest_id, transition_delay_ms=2000, run_once=False)
FSMVariables.fsm.AddState(name="Accepting Quest Reward", execute_fn=lambda: Routines.CompleteQuest(), exit_condition=lambda: Map.GetMapID() == gtob and not Map.IsMapLoading() and Map.IsMapReady() and not Quest.GetActiveQuest() == ha_quest_id, transition_delay_ms=2000, run_once=False)
FSMVariables.fsm.AddState(name="Adding Henchies", execute_fn=lambda: Routines.AddHenchmen(), exit_condition=lambda: Party.GetPartySize() >= 8, transition_delay_ms=1000,)
FSMVariables.fsm.AddState(name="Checking Balth Points", execute_fn=lambda: Routines.BuyZkeys(), exit_condition=lambda: not Agent.IsMoving(Player.GetAgentID()), transition_delay_ms=5000, run_once=True)
FSMVariables.fsm.AddState(name="Buying from Tolkano", execute_fn=lambda: Routines.SendDialogs(), exit_condition=lambda: Player.GetBalthazarData()[0] < 5000 or BotVariables.interaction_stage > 3, transition_delay_ms=5000, run_once=False, )
FSMVariables.fsm.AddState(name="Entering HA Mission", execute_fn=lambda: Routines.EnterMission(), exit_condition=lambda: Map.GetMapID() == heroes_ascent and Map.IsExplorable() and not Map.IsMapLoading() and Map.IsMapReady(), transition_delay_ms=1000, run_once=True)
FSMVariables.fsm.AddState(name="Zaishen", execute_fn=lambda: Routines.Zaishen(), exit_condition=lambda: Map.GetMapID() == underworld and not Map.IsMapLoading() and Map.IsMapReady(), transition_delay_ms=15000, run_once=False)
FSMVariables.fsm.AddState(name="Underworld", execute_fn=lambda: Routines.Underworld(), exit_condition=lambda: Map.GetMapID() != underworld and not Map.IsMapLoading() and Map.IsMapReady(), transition_delay_ms=5000, run_once=False)
FSMVariables.fsm.AddState(name="Fetid River", execute_fn=lambda: Routines.Fetid_River(), exit_condition=lambda: Map.GetMapID() != fetid_river and not Map.IsMapLoading() and Map.IsMapReady(), transition_delay_ms=5000, run_once=False)
FSMVariables.fsm.AddState(name="Burial Mounds", execute_fn=lambda: Routines.Burial_Mounds(), exit_condition=lambda: Map.GetMapID() != burial_mounds and not Map.IsMapLoading() and Map.IsMapReady(), transition_delay_ms=5000, run_once=False)

class Combat:
    @staticmethod
    def CastSpell(slot, target_agent_id):
        
        skill_id = SkillBar.GetSkillIDBySlot(slot)
        cost = Skill.Data.GetEnergyCost(skill_id)
        skill_state = SkillBar.GetSkillData(slot)
        skill_name = Skill.GetName(skill_id)
       
        my_energy = Combat.GetMyEnergy()
        
       # Py4GW.Console.Log("Combat", f"Trying UseSkill(slot={slot}, target={target_agent_id}) (skill_id={skill_id}), my energy={my_energy}, cost={cost}")

        if my_energy < cost:
            #Py4GW.Console.Log("Combat", "Not enough energy to cast skill " + str(skill_name))
            return
        if not skill_state.recharge == 0:
            #Py4GW.Console.Log("Combat", str(skill_name) + " failed to cast, Skill not ready")
            return
        if not target_agent_id or target_agent_id == 0:
            #Py4GW.Console.Log("Combat", "No target to cast skill " + str(skill_name))
            return
        else:
            #Py4GW.Console.Log("Combat", f"Casting {skill_name} on target {Agent.GetName(target_agent_id)}")
           
            SkillBar.UseSkill(slot, target_agent_id)
            return 
        
    @staticmethod
    def GetMyEnergy():
        player_agent_id = Player.GetAgentID()
        energy = Agent.GetEnergy(player_agent_id)
        max_energy = Agent.GetMaxEnergy(player_agent_id)
        my_energy = int(energy * max_energy)
        return my_energy
    
    @staticmethod
    def IsRecharged(skill_slot):
        skill = SkillBar.GetSkillData(skill_slot)
        recharge = skill.recharge
        return recharge == 0
    
    @staticmethod
    def GetSpellRangeEnemies(enemies_array):
        return AgentArray.Filter.ByDistance(enemies_array, Player.GetXY(), Range.Spellcast.value)
    
    @staticmethod
    def GetAliveEnemies():
        all_enemies = AgentArray.GetEnemyArray()
        return AgentArray.Filter.ByCondition(all_enemies, lambda agent_id: Agent.IsAlive(agent_id))
    
    @staticmethod
    def AmIMoving():
        my_id = Player.GetAgentID()
        return Agent.IsMoving(my_id)
    
    @staticmethod
    def MoveToXYWithRandomness(x, y, randomness):
        random_x = x + random.randint(-randomness, randomness)
        random_y = y + random.randint(-randomness, randomness)
        Player.Move(random_x, random_y)
        
    @staticmethod
    def GetTeamColorBySpawnPoint(spawn_xy, spawn_color, player_xy, radius=500):
        """
        !!! NOT IMPLEMENTED OR USED AT ALL !!!
        Returns the spawn_color if player is within the radius of spawn_xy.
        Otherwise, returns the opposite color.
        Args:
            spawn_xy: coordinates of spawn point when you first load into map.
            spawn_color: must match correctly the color of the given spawn_xy point, eg: "red" or "blue".
            player_xy: should also be the xy of the Player as spawned in map.  eg: Player.GetXY()
        """
        dx = spawn_xy[0] - player_xy[0]
        dy = spawn_xy[1] - player_xy[1]
        distance_squared = dx * dx + dy * dy

        if distance_squared <= radius * radius:
            return spawn_color
        else:
            return 'Blue' if spawn_color == 'Red' else 'Red'
        
        
def DrawWindow():
    global bot_vars, fsm_vars

    PyImGui.begin("HA BOT")
    PyImGui.text("State: " + BotVariables.state)
    fsm_state = FSMVariables.fsm.get_current_step_name() or "None"
    PyImGui.text("FSM State: " + fsm_state)

    BotVariables.ha_quest_button_state = PyImGui.checkbox("HA Quest", BotVariables.ha_quest_button_state)
    
    PyImGui.separator()
    BotVariables.stop_buying_keys_button_state = PyImGui.checkbox("Stop Buying Keys", BotVariables.stop_buying_keys_button_state)   
   
    PyImGui.separator()
    BotVariables.wait_for_fame_button_state = PyImGui.checkbox("Wait for fame before leaving burial", BotVariables.wait_for_fame_button_state)    
   
    PyImGui.separator()

    if BotVariables.state == "Sleeping":
        if PyImGui.button("Start"):
            FSMVariables.fsm.reset()
            FSMVariables.fsm.start()
            BotVariables.state = "Running"
            
    elif PyImGui.button("Stop"):
        FSMVariables.fsm.stop()
        BotVariables.state = "Sleeping"
            
def main():
    try:
        if Map.IsMapReady() and Party.IsPartyLoaded() and not Map.IsMapLoading():
            DrawWindow()
            if BotVariables.state == "Stopped":
                FSMVariables.fsm.stop()
            if BotVariables.state == "Running":
                if BotVariables.restart_fsm:
                    FSMVariables.fsm.stop()
                    FSMVariables.fsm.reset()
                    FSMVariables.fsm.start()
                    BotVariables.restart_fsm = False
                else:
                    FSMVariables.fsm.update()

    except Exception as e:
        Py4GW.Console.Log("main loop", "error in main loop: " + str(e))

    
    
if __name__ == "__main__":
    main()
