import YanAPI

robot_ip = "192.168.1.22"
YanAPI.yan_api_init(robot_ip)
batt = YanAPI.get_robot_battery_value()
pcTTS = "Hi. Connection Successful, Battery percentage is %s" %batt
YanAPI.start_voice_tts(pcTTS)

YanAPI.set_servos_angles(angles={"LeftShoulderFlex": 90},runtime= 500)

YanAPI.start_play_motion(name="reset", version = "v1")