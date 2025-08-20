import YanAPI

robot_ip = "192.168.1.15"
YanAPI.yan_api_init(robot_ip)
batt = YanAPI.get_robot_battery_value()
#YanAPI.start_play_motion(name="reset", version = "v1")
#pcTTS = "Hi. Connection Successful, Battery percentage is %s" %batt
#pcTTS = "Hi Mae. Please dance for us"
#YanAPI.start_voice_tts(pcTTS)
print(batt)


#YanAPI.set_servos_angles_layers(data={"RightShoulderRoll":{90, 400}})
#YanAPI.set_servos_angles(angles={"RightShoulderRoll":0}, runtime=400)
#YanAPI.set_servos_angles(angles={"RightShoulderFlex":180}, runtime=400)
#YanAPI.set_servos_angles(angles={"RightElbowFlex":160}, runtime=400)

#YanAPI.set_servos_angles(angles={"LeftShoulderRoll":0}, runtime=400)
#YanAPI.set_servos_angles(angles={"LeftShoulderFlex":180}, runtime=400)
#YanAPI.set_servos_angles(angles={"LeftElbowFlex":160}, runtime=400)


#YanAPI.start_play_motion(name="reset", version = "v1")