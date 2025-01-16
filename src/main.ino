#include <Arduino.h>
#include <BLEDevice.h>
#include <esp_sleep.h>

#define SLEEP_TIME 30 // Time in seconds

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("Starting setup...");

  // Initialize BLE
  BLEDevice::init("");
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();

  // Minimal advertising setup
  BLEAdvertisementData advertisementData;
  advertisementData.setFlags(0x1A); // General discoverable mode, BR/EDR not supported
  pAdvertising->setAdvertisementData(advertisementData);

  // Start advertising
  Serial.println("Starting BLE advertising...");
  pAdvertising->start();
  delay(100); // Allow advertisement for a short duration
  pAdvertising->stop();
  Serial.println("BLE advertising stopped.");

  // Enter deep sleep
  Serial.println("Entering deep sleep...");
  esp_sleep_enable_timer_wakeup(SLEEP_TIME * 1000000); // Convert to microseconds
  esp_deep_sleep_start();
}

void loop() {
  // Not used since the device will enter deep sleep
}

