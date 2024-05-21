import re
import os
import gpio as GPIO
import time
import subprocess
import sys
import socket
import pyttsx3
from pydub import AudioSegment

sys.path.insert(0, '/home/rock/Desktop/Hearsight/')
from config import *
from play_audio import GTTSA

play_file = GTTSA()

GPIO.setup(450, GPIO.IN)
GPIO.setup(421, GPIO.IN)
GPIO.setup(447, GPIO.IN)
GPIO.setup(448, GPIO.IN)

engine = pyttsx3.init()
#engine.setProperty('voice', 'english_rp+f3')
#engine.setProperty('rate', 120)
engine.setProperty('voice', 'en-gb')
engine.setProperty('rate', 140)

#os.system('pkill adb')
subprocess.run(['pkill', 'adb'])  # Kill adb process

essids = []# Define essids outside the main function

def find_wireless_interface():
    try:
        result = os.popen('iw dev | grep Interface').read()
        interface = result.split(' ')[1].strip()
        return interface
    except Exception as e:
        print(f"An error occurred while finding the wireless interface: {e}")
        play_file.play_audio_file("no_WiFi_networks_found_enable_mobile_hotspot_and_try_again.mp3")
#        play_file.play_audio_file("Thank You.mp3")
        time.sleep(0.3)
#        return None
        sys.exit()

def extract_essids(result):
    return [line.split('"')[1] for line in result.split('\n') if 'ESSID' in line]

def connect_to_wifi(ssid, password):
    try:
        play_file.play_audio_file("connecting.mp3")
        os.system(f"nmcli device wifi connect '{ssid}' password '{password}'")
        play_file.play_audio_file("340Hz-5sec.wav")
        print(f"Connected to WiFi network: {ssid}")
        ipv4_address = get_ipv4_address()  # Get and print the IPv4 address after connection
        print(ipv4_address)
        if ipv4_address:
            try:
                connect_and_send_ip()
                start_server()
                
            except Exception as send_ip_error:
                print(f"Error during connect_and_send_ip: {send_ip_error}")
#                play_file.play_audio_file("no_WiFi_networks_found_enable_mobile_hotspot_and_try_again.mp3")
#                time.sleep(0.3)
#                return None
                sys.exit()

        else:
            print("IPv4 address not available.")
            play_file.play_audio_file("no_WiFi_networks_found_enable_mobile_hotspot_and_try_again.mp3")
            # play_file.play_audio_file("Thank You.mp3")
            time.sleep(0.3)
#            return None
            sys.exit()

    except Exception as wifi_connection_error:
        print(f"Error during WiFi connection: {wifi_connection_error}")
#        play_file.play_audio_file("no_WiFi_networks_found_enable_mobile_hotspot_and_try_again.mp3")
#        time.sleep(0.3)
#        return None
        sys.exit()
    
def get_ipv4_address():
    try:
        result = subprocess.check_output(["ip", "-4", "address", "show", "dev", "wlan0"]).decode("utf-8")
        ipv4_address = result.split("inet ")[1].split("/")[0]  # Extract the IPv4 address from the result
        return ipv4_address
    except Exception as e:
        print(f"Error: {e}")
#        play_file.play_audio_file("no_WiFi_networks_found_enable_mobile_hotspot_and_try_again.mp3")
#        time.sleep(0.3)
#        return None
        sys.exit()

def connect_and_send_ip():
    try:
        debian_ip = get_ipv4_address()  # Get Debian Buster 10 IP address
        if debian_ip:
            try:
#                subprocess.run(['adb', 'shell', f'echo {debian_ip} > /sdcard/debian_ip.txt'], check=True) # Send IP address to Android device over USB
                subprocess.run(['adb', 'shell', f'mkdir -p /sdcard/ip{debian_ip}'])# Send IP address to Android device over USB
#                subprocess.run(['adb', 'shell', f'echo {debian_ip} > /sdcard/ip{debian_ip}/debian_ip.txt'], check=True)# Send IP address to Android device over USB
                
            except subprocess.CalledProcessError as e:
                print(f"Error sending IP address to Android device: {e}")
#                play_file.play_audio_file("no_WiFi_networks_found_enable_mobile_hotspot_and_try_again.mp3")
#                time.sleep(0.3)
#                return None
                sys.exit()
        else:
            print("IPv4 address not available.")
            play_file.play_audio_file("no_WiFi_networks_found_enable_mobile_hotspot_and_try_again.mp3")
            # play_file.play_audio_file("Thank You.mp3")
            time.sleep(0.3)
#            return None
            sys.exit()

    except Exception as error:
        print(f"An error occurred: {error}")
#        play_file.play_audio_file("no_WiFi_networks_found_enable_mobile_hotspot_and_try_again.mp3")
#        time.sleep(0.3)
#        return None
        sys.exit()

def start_server():
    try:
        play_file.play_audio_file("340Hz-5sec.wav")
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)# Create a socket object
#        host = socket.gethostbyname(socket.gethostname())# Get the IP address of the server
        host = get_ipv4_address()  # Get Debian Buster 10 IP address & Get the IP address of the server
        print('Server IP address:', host)
        port = 12341# Define the port on which you want to listen        
        server_socket.bind((host, port))# Bind to the port        
        server_socket.listen(5)# Queue up to 5 requests
        play_file.play_audio_file("please_go_to_the_hearsight_app_and_click_on_connect_to_device.mp3")
        
        while True:                
            client_socket, addr = server_socket.accept()# Establish connection with a single client
            print('Got connection from', addr)          
            try:
                message = client_socket.recv(1024).decode('utf-8')# Receive the message from the client
                print(message)
                
                if message.strip() == "connecttodevice":# Check if the received message matches a specific string
                    try:
                        play_file.play_audio_file("hearsight_app_connected.mp3")
                                                
                    except Exception as play_error:
                        print(f"Error playing audio file: {play_error}")
#                        play_file.play_audio_file("no_WiFi_networks_found_enable_mobile_hotspot_and_try_again.mp3")
                        # play_file.play_audio_file("Thank You.mp3")
#                        time.sleep(0.3)
#                        return None
                        sys.exit()
                        
                elif message.strip() == "disconnecttodevice":# Check if the received message matches a specific string
                    try:
                        disconnect_from_wifi()  # Disconnect from WiFi when exit button is pressed
                        delete_files_in_directory('/etc/NetworkManager/system-connections/')
                        client_socket.close()  # Close the connection with the client
                        server_socket.close()  # Close the server socket
                        # List folders on the Android device
                        result = subprocess.run(['adb', 'shell', 'ls', '/sdcard'], capture_output=True, text=True)
                        folder_list = result.stdout.split('\n')
                        # Delete folders that match the pattern
                        for folder in folder_list:
                            if folder.strip() and re.match(r'ip[\w.]*', folder.strip()):
                                subprocess.run(['adb', 'shell', 'rm', '-r', f'/sdcard/{folder.strip()}'])
                                print(f"Deleted folder: {folder.strip()} on Android device.")
                        time.sleep(1)
                        sys.exit()
                                                
                    except Exception as play_error:
                        print(f"Error playing audio file: {play_error}")
#                        play_file.play_audio_file("no_WiFi_networks_found_enable_mobile_hotspot_and_try_again.mp3")
                        # play_file.play_audio_file("Thank You.mp3")
#                        time.sleep(0.3)
#                        return None
                        sys.exit()
                    
                else:
                    try:
                        os.system(message)
                        debian_ip = get_ipv4_address()  # Get Debian Buster 10 IP address
                        subprocess.run(['adb', 'shell', f'rm -r /sdcard/ip{debian_ip}'])# Delete IP address to Android device over USB
                        connect_and_send_ip()
                        share(message)
                                               
                    except Exception as play_error:
                        print(f"Error playing audio file: {play_error}")
#                        play_file.play_audio_file("no_WiFi_networks_found_enable_mobile_hotspot_and_try_again.mp3")
                        # play_file.play_audio_file("Thank You.mp3")
#                        time.sleep(0.3)
#                        return None
                        sys.exit()

            except ConnectionResetError:
                print("Connection with the client was reset.")
#                play_file.play_audio_file("no_WiFi_networks_found_enable_mobile_hotspot_and_try_again.mp3")
                # play_file.play_audio_file("Thank You.mp3")
#                time.sleep(0.3)
#                return None
                sys.exit()

            except Exception as recv_error:
                print(f"Error receiving message: {recv_error}")
#                play_file.play_audio_file("no_WiFi_networks_found_enable_mobile_hotspot_and_try_again.mp3")
                # play_file.play_audio_file("Thank You.mp3")
#                time.sleep(0.3)
#                return None
                sys.exit()

    #        finally:
    #            client_socket.close()# Close the connection with the client
    #            print('hai')

    except Exception as server_error:
        print(f"Error setting up the server: {server_error}")
        play_file.play_audio_file("hold_on_connection_in_progress_initiating_shortly.mp3")
        # play_file.play_audio_file("Thank You.mp3")
#        time.sleep(0.3)
#        return None
        sys.exit()

#    finally:
#        server_socket.close()# Close the server socket
#        print('bye')
#        return None

def share(message):
    try:
        determine_audio_category(message)

    except Exception as e:
        print(f"An error occurred: {e}")
        
def determine_audio_category(message):
    if "document_audios" in message:
        play_file.play_audio_file("stored_in_document.mp3")
        files = os.listdir('/home/rock/Desktop/Hearsight/English/online_features/document_audios/')
        total_files = len(files)
        print('Total files in document_audios:', total_files)
        play_file.play_audio_file("total_files.mp3")
        engine.say(total_files)
        engine.runAndWait()
       
    else:
        play_file.play_audio_file("stored_in_media.mp3")
        files = os.listdir('/home/rock/Desktop/Hearsight/English/online_features/media_audios/')
        total_files = len(files)
        print('Total files in media_audios:', total_files)
        play_file.play_audio_file("total_files.mp3")
        engine.say(total_files)
        engine.runAndWait()
        
#def handle_exit_button():
#    play_file.play_audio_file("exit_button_pressed.mp3")
#    disconnect_from_wifi()  # Disconnect from WiFi when exit button is pressed
#    # delete_files_in_directory('/etc/NetworkManager/system-connections/')
#    client_socket.close()  # Close the connection with the client
#    server_socket.close()  # Close the server socket
#    time.sleep(1)
#    sys.exit()  # Assuming you want to exit the program

def disconnect_from_wifi():
    try:
        os.system("nmcli device disconnect wlan0")
        print("Disconnected from WiFi")
        play_file.play_audio_file("hearsight_app_disconnected.mp3")
    except Exception as e:
        print(f"Error disconnecting from WiFi: {e}")
#        return None
        sys.exit()

def delete_files_in_directory(directory_path):
    try:
        files = os.listdir(directory_path)
        for file_name in files:
            file_path = os.path.join(directory_path, file_name)
            os.remove(file_path)
            print(f"Deleted file: {file_path}")
        print("All files deleted successfully.")
    except Exception as e:
        print(f"Error: {e}")
#        return None
        sys.exit()

def main():
    global essids
    
#    subprocess.run(['adb', 'devices'])  # List adb devices
    
    # List folders on the Android device
    result = subprocess.run(['adb', 'shell', 'ls', '/sdcard'], capture_output=True, text=True)
    folder_list = result.stdout.split('\n')
    # Delete folders that match the pattern
    for folder in folder_list:
        if folder.strip() and re.match(r'ip[\w.]*', folder.strip()):
            subprocess.run(['adb', 'shell', 'rm', '-r', f'/sdcard/{folder.strip()}'])
            print(f"Deleted folder: {folder.strip()} on Android device.")

    try:
        subprocess.run(['adb', 'devices'])  # List adb devices
        interface = find_wireless_interface()

        if interface:
            try:
                result = os.popen(f'iwlist {interface} scan | grep ESSID').read()
                essids = extract_essids(result)
                print(f"Number of available WiFi networks: {len(essids)}")
                print("ESSIDs:", essids)
            except Exception as scan_error:
                print(f"Error during WiFi network scanning: {scan_error}")
#                play_file.play_audio_file("no_WiFi_networks_found_enable_mobile_hotspot_and_try_again.mp3")
                # play_file.play_audio_file("Thank You.mp3")
#                time.sleep(0.3)
#                return None
                sys.exit()
        else:
            print("Wireless interface not found.")
            play_file.play_audio_file("no_WiFi_networks_found_enable_mobile_hotspot_and_try_again.mp3")
            # play_file.play_audio_file("Thank You.mp3")
            time.sleep(0.3)
#            return None
            sys.exit()            
    except Exception as find_interface_error:
        print(f"An error occurred during finding the wireless interface: {find_interface_error}")
#        play_file.play_audio_file("no_WiFi_networks_found_enable_mobile_hotspot_and_try_again.mp3")
        # play_file.play_audio_file("Thank You.mp3")
#        time.sleep(0.3)
#        return None
        sys.exit()

if __name__ == "__main__":
    main()

    if not essids:
        play_file.play_audio_file("no_WiFi_networks_found_enable_mobile_hotspot_and_try_again.mp3")
        time.sleep(1)
        sys.exit()
    else:
        play_file.play_audio_file("press your feature button now.mp3")
        limit = len(essids)
        count = -1

        while True:
            time.sleep(0.0001)
            forward = GPIO.input(450)
            backward = GPIO.input(421)

            if forward:
                count = (count + 1) % limit
                print(count)
            if backward:
                count = (count - 1) % limit
                print(count)

            if forward or backward:
                selected_essid = essids[count]
                print(f"Selected WiFi network: {selected_essid}")
                engine.say(selected_essid)
                engine.runAndWait()

            input_state = GPIO.input(447)
            if input_state == True:
#                time.sleep(0.3)
                play_file.play_audio_file("feature_confirmed.mp3")
#                os.system('adb devices')
#                subprocess.run(['adb', 'devices'])  # List adb devices
                ssid = selected_essid
                password = "hearsight"
#                subprocess.run(['adb', 'devices'])  # List adb devices
                connect_to_wifi(ssid, password)# Call the function to connect to WiFi
            
            input_state = GPIO.input(448)
            if input_state == True:
                play_file.play_audio_file("feature_exited.mp3")
                disconnect_from_wifi()# Disconnect from WiFi when exit button is pressed                
                delete_files_in_directory('/etc/NetworkManager/system-connections/')
                client_socket.close()# Close the connection with the client
                server_socket.close()# Close the server socket
                # List folders on the Android device
                result = subprocess.run(['adb', 'shell', 'ls', '/sdcard'], capture_output=True, text=True)
                folder_list = result.stdout.split('\n')
                # Delete folders that match the pattern
                for folder in folder_list:
                    if folder.strip() and re.match(r'ip[\w.]*', folder.strip()):
                        subprocess.run(['adb', 'shell', 'rm', '-r', f'/sdcard/{folder.strip()}'])
                        print(f"Deleted folder: {folder.strip()} on Android device.")
                time.sleep(1)
                break
