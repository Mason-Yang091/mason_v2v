import sys
import time
import threading
import json
import os
import platform
import keyboard
import select
import termios
import tty


from src.func.record_audio import *
from src.func.record_voice import *
from src.func.txt_to_wav import * 
from src.func.wav_to_txt import *
from src.func.all_import import *
from src.func.play_audio import *
###connection###
from src.server_client.client import *
from src.server_client.server import *
###display###
from src.server_client.screen import *
from PySide6.QtWidgets import *
###API###
from src.func.api import *


"""
export QT_QPA_PLATFORM=offscreen

"""


receive_or_not = False

state = "await"
received_queue = []  # 儲存多個收到的 json 訊息
flush_stdin = False  # 控制是否忽略 stdin 輸入

# === 跨平台輸入處理 ===
if platform.system() == "Windows":
    import msvcrt
else:
    import select
    import termios
    import tty
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setcbreak(sys.stdin.fileno())

def is_tab_pressed():
    if platform.system() == "Windows":
        if msvcrt.kbhit():
            key = msvcrt.getwch()
            return key == '\t'
        return False
    else:
        dr, _, _ = select.select([sys.stdin], [], [], 0)
        if dr:
            key = sys.stdin.read(1)
            return key == '\t'
        return False

def restore_stdin():
    if platform.system() != "Windows":
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def state_monitor():
    global state, flush_stdin, receive_or_not
    while True:
        if not flush_stdin and is_tab_pressed():
            state = "sender"
            flush_stdin = True

        elif receive_or_not:
            state = "receiver"


        if state == "sender":
            print("[狀態] sender → 執行 sender_start()")
            sender_start()
            state = "await"
            flush_stdin = False

        elif state == "receiver":
            print(f"[狀態] receiver → 處理 ")
            receiver_start()
            state = "await"
            receive_or_not = False


        time.sleep(0.1)

def receiver_start():

    # convert json to text
    # api_json_to_txt(input_path='receiver_tmp/received.json' , output_path='receiver_tmp/received.txt')
    #json_to_txt_pipeline(input_path='receiver_tmp/received.json', output_path='receiver_tmp/received.txt')
    # convert text to voice
    txt_to_wav(input_path='receiver_tmp/received.txt', output_path='receiver_tmp/received.wav')
    # play the audio
    play_audio('receiver_tmp/received.wav')
    # wait for receiver to confirm



def sender_start():
    record_audio(filename='sender_tmp/sender.wav', fs=44100, channels=2, max_seconds=300)
    wav_to_txt(input_path='sender_tmp/sender.wav', output_path='sender_tmp/sender.txt')
    
    #tested while record_audio fucked up
        # with open('sender_tmp/sender.txt', 'r', encoding='utf-8') as f:
        #     content = f.read()
        #     print("[Transcript] sender.txt內容如下：")
        #     print(content)

        # with open('sender_tmp/sender.txt', 'w', encoding='utf-8') as f:
        #     content = "我是ANK1234,想要超車你GCC3456 "
        #     f.write(content) 

    with open('sender_tmp/sender.txt', 'r', encoding='utf-8') as f:
            content = f.read()
            print("[Transcript] sender.txt內容如下：")
            print(content)

    api_txt_to_json( input_path= 'sender_tmp/sender.txt', output_path= 'sender_tmp/sender.json')

    with open('sender_tmp/sender.json', 'r', encoding='utf-8') as f:
        sender_data = json.load(f)
        print(sender_data)
        correctness = sender_data.get("correctness", 0)  # 若沒這欄位則預設為 0
    #correctness = 1
    
    print(correctness)

    if correctness == '1':
        api_json_to_txt(input_path='sender_tmp/sender.json', output_path='sender_tmp/check.txt')
        #my_check.txt =  "  "+check.txt
        with open('sender_tmp/sender.json', 'r', encoding='utf-8') as f:
            sender_data = json.load(f)
            target_id = sender_data.get("傳給的車牌號碼", "未知車牌")

        # 讀 check.txt 內容
        with open('sender_tmp/check.txt', 'r', encoding='utf-8') as f:
            check_content = f.read().strip()

        # 合併內容
        final_text = f"目標車輛是 {target_id} {check_content}"

        # 寫入 my_check.txt
        with open('sender_tmp/my_check.txt', 'w', encoding='utf-8') as f:
            f.write(final_text)

        txt_to_wav(input_path='sender_tmp/my_check.txt', output_path='sender_tmp/my_check.wav')
        
        play_audio('sender_tmp/my_check.wav')

        

        ####
        user_choice = wait_for_user_input(timeout=10)

        if user_choice == "restart":
            print("[Info] 使用者選擇重錄或超時未操作，重新開始錄音。")
            sender_start()
            return  # 終止當前流程，避免繼續往下執行
        else:
            print("[Info] 使用者確認內容，繼續傳送。")
        ###

        #check finish
        # 讀取 sender.json，取得目標車牌號碼
        with open('sender_tmp/sender.json', 'r', encoding='utf-8') as f:
            sender_data = json.load(f)
            target_id = sender_data.get("傳給的車牌號碼")

        # 讀取 check.txt 作為訊息內容
        with open('sender_tmp/check.txt', 'r', encoding='utf-8') as f:
            message = f.read()

        # 傳送
        if target_id:
            send_to(target_id, message)
            print("sented!")
        else:
            print("[Error] 找不到車牌號碼")
    

    #correctness = 0
    else : 
        print("record again")
        sender_start()
        return  # 終止當前流程，避免繼續往下執行

 
def wait_for_user_input(timeout=10):
    print(f"[請在 {timeout} 秒內按空白鍵確認，或直接 Enter 取消]")
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        start = time.time()
        buffer = ""
        while time.time() - start < timeout:
            if select.select([sys.stdin], [], [], 0.1)[0]:
                ch = sys.stdin.read(1)
                if ch == '\n':
                    if buffer == "":
                        print("[Enter] 被取消，重錄。")
                        return "restart"
                    elif buffer == " ":
                        print("[空白鍵] 確認，繼續執行。")
                        return "continue"
                    else:
                        print("[其他鍵] 被當作取消，重錄。")
                        return "restart"
                else:
                    buffer += ch
        print("[Timeout] 沒有輸入，重錄。")
        return "restart"
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)



def handle_incoming(data):
    global receive_or_not
    receive_or_not = True
    print(f"[Main got message] {data}")
    # 指定儲存的目錄和檔案名稱
    directory = "receiver_tmp"
    filename = "received.txt"
    filepath = os.path.join(directory, filename)
    
    # 將 json_data 寫入檔案
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(data)

    ### there should call a function to do sth



if __name__== "__main__":
    ##set CarID
    carID = input('your car ID: ')
    set_car_id(carID)
    ##設定receiver function註冊
    set_on_message_callback(handle_incoming)
    ##接上server
    connect_with_retry()

    ###   display   ###
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    threading.Thread(target=state_monitor, daemon=True).start()
    threading.Thread(target=sio.wait, daemon=True).start()

    # try:
    
    #關螢幕等於關機
    sys.exit(app.exec())