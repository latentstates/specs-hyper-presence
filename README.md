# Documentation for ESP32 Beacon

## Description of ESP32 Beacon

### About
BLE (Bluetooth Low Energy) beacons are wearable pendants containing a small electronic circuit that emits Bluetooth frames with its unique MAC address (e.g., `34:12:A4:5E:33:44`). These frames can be captured by scanning stations located at predefined locations.

### Components
**Our setup includes:**
- **ESP32-C3:** Xiao from Seeed Studio ([link](https://www.seeedstudio.com/Seeed-XIAO-ESP32C3-p-5431.html)), $4.99.
- **Battery:** 3.7V LiPo, either 200mAh or 100mAh:
  - 200mAh battery ([link](https://www.seeedstudio.com/Seeed-XIAO-ESP32C3-p-5431.html)) - $2.10 per unit (for a batch of 100 units).
  - 100mAh battery - $1.28 per unit (for a batch of 100 units).
- **Battery Connector:** PH2 (2mm), available [here](https://fr.aliexpress.com/item/1005006916797356.html) at approximately $0.25 each (potentially cheaper in bulk).

**Total cost:** $7.35 per unit for the basic circuit (excluding shipping costs).

---

## Power

The circuit can be powered via USB-C or a battery. The Xiao ESP32-C3 includes battery pads underneath, where a battery PH2 connector can be soldered (ensure correct polarity: +red, -black).

### Key Notes:
- The Xiao ESP32-C3 does not light its LEDs when running from battery power; this is normal.
- If both a battery and USB-C are connected, the Xiao will charge the battery.
- The Xiao does not monitor battery charge levels.

### Measured Power Consumption:
Power consumption measured while running under USB-C power:
- **1.6mA**

Battery consumption may vary; further testing is needed.

---

## Batteries

### 100mAh Battery:
- **Autonomy:** ~62 hours
- **Dimensions:**
  - Length: 22.0 mm
  - Width: 11.0 mm
  - Thickness: 6.0 mm
- **Capacity:** 100mAh

### 200mAh Battery:
- **Autonomy:** ~124 hours
- **Dimensions:**
  - Length: 27.0 mm
  - Width: 20.0 mm
  - Thickness: 5.5 mm
- **Capacity:** 200mAh

---

## Charging

Changing and managing multiple batteries can be time-consuming. To simplify the process and avoid mixing charged and discharged batteries, consider a multi-port charger:
- **6x Charger:** Available [here](https://www.drone-fpv-racer.com/en/emax-charger-6-ports-1s-lipo-ph20-7923.html?gQT=1) (€11.90).

---

## Code

The program for the beacon is available [here (link to be added)](https://www.url.com).

### Program Behavior:
- This program runs automatically once the Xiao ESP32-C3 is powered (via USB-C or battery).
- It emits Bluetooth beacon frames containing the unique MAC address.
- The device goes into deep sleep for 30 seconds to conserve battery.
- It wakes up, sends another frame, and goes back to sleep.
- These beacon signals can be captured by scanning stations placed around the event area.

---

## How to Flash the Code to the Xiao ESP32-C3

The following methods have been tested on Linux using PlatformIO but should be adaptable for macOS and Windows or using the Arduino IDE.

### Using PlatformIO:
1. Clone the repository.
2. Install PlatformIO.
3. Connect the Xiao device via USB-C.
4. If needed, fix permissions for the USB port.
5. Run the command:
   ```sh
   pio run -t upload
   ```

### Using Arduino IDE:
(Add specific instructions here, if applicable.)

---

## Process for the Experiment

1. **Participant Setup:**
   - Explain the experiment to the volunteer.
   - Ensure the participant has filled out the informed consent form and has a unique participant ID.

2. **Prepare Beacons:**
   - Have beacons open and batteries charged.
   - When a participant begins the experiment, connect a battery to the beacon’s chip, and securely close it.

3. **Testing:**
   - Place the beacon on a booth reader.
   - Open the app to confirm the beacon is recognized. If the app shows the current necklace on the booth reader, proceed.
   - If not recognized, set the beacon and battery aside (e.g., in a Faraday cage) for later inspection, and use a different beacon.

4. **Assigning the Beacon:**
   - Associate the beacon with the participant’s ID using the app.
   - Give the beacon to the participant, asking them to return it at the end of the experiment. A designated collection point (e.g., a metallic letterbox) should be available at the experiment’s location.

5. **Start the Experiment:**
   - Once the beacon is successfully set up, the participant can begin the experiment.
