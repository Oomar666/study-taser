# study-taser

A custom hardware and computer vision productivity tool designed to monitor study sessions and physically enforce focus. 

This project bridges software-based visual detection with physical hardware actuation to create an interactive, automated environment.

##  Features
* **Real-Time Computer Vision:** Monitors user presence and focus using [mention the library, e.g., OpenCV / Python / C++].
* **Hardware Actuation:** Triggers a physical response system when a lack of focus or absence is detected.
* **Custom Control Logic:** Microcontroller-based communication bridging the PC's vision processing and the physical hardware.

##  Hardware & Components Used
* **MicrocontrollerE:**  ESP32-S3
* **Vision / Input:**    Standard Web camera
* **Actuation Mechanism:** [ Relays, vibration motor, step-down converter5V]
* **Other Electronics:** [ prefboard, jumper wires, 8v battery]

##  Software Stack
* **Language:** [ Python / C++]
* **Libraries:** [ OpenCV, MediaPipe, pyserial]
* **Communication Protocol:** [ Serial / UART communication between PC and microcontroller]

##  How It Works
1. The camera feeds real-time video to the computer vision script.
2. The script processes the frames to detect [e.g., eye tracking, face presence, phone detection, browser content].
3. If the user loses focus for [X] seconds, a signal is sent via Serial to the microcontroller.
4. The microcontroller triggers the hardware relay/mechanism.

##  Project Media
*(Add a photo of your physical hardware setup or a short GIF of the computer vision working here)*
![Project Setup](link-to-your-image.jpg)

##  Future Improvements
* [e.g., Build a custom PCB to replace the breadboard]
* [e.g., Add a GUI for adjusting the focus timer]
* [e.g., Implement 3D printed housing for the components]