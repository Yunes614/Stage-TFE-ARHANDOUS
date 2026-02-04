// ===============================
// Bibliothèques
// ===============================
#include <Arduino.h>
#include <Wire.h>
#include <hd44780.h>
#include <hd44780ioClass/hd44780_I2Cexp.h>
#include <DHT.h>
#include <Adafruit_NeoPixel.h>

// ===============================
// Définitions des broches
// ===============================
#define PRESSURE_PIN 25
#define BUTTON_PIN 13
#define LED_GREEN_PIN 2
#define LED_RED_PIN 15
#define DHT_PIN 26
#define DHTTYPE DHT22
#define PIN_RGB 33
#define NUM_PIXELS 90

#define RED_PIN 27
#define GREEN_PIN 14
#define BLUE_PIN 12

// ===============================
// Objets
// ===============================
Adafruit_NeoPixel strip(NUM_PIXELS, PIN_RGB, NEO_GRB + NEO_KHZ800);
hd44780_I2Cexp lcd(0x27);
DHT dht(DHT_PIN, DHTTYPE);

// ===============================
// PWM RGB
// ===============================
const int redChannel = 0;
const int greenChannel = 1;
const int blueChannel = 2;
const int freq = 2000;
const int resolution = 8;

// ===============================
// Variables globales
// ===============================
int last_capteur_value = 0;
int previousButtonState = HIGH;
bool envoiAuto = false;

// ===============================
// SETUP
// ===============================
void setup() {
  Serial.begin(115200);
  Wire.begin();

  lcd.begin(16, 2);
  lcd.setBacklight(255);

  strip.begin();
  strip.show();
  strip.setBrightness(50);

  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(LED_RED_PIN, OUTPUT);
  pinMode(LED_GREEN_PIN, OUTPUT);

  ledcSetup(redChannel, freq, resolution);
  ledcSetup(greenChannel, freq, resolution);
  ledcSetup(blueChannel, freq, resolution);

  ledcAttachPin(RED_PIN, redChannel);
  ledcAttachPin(GREEN_PIN, greenChannel);
  ledcAttachPin(BLUE_PIN, blueChannel);

  dht.begin();

  ledcWrite(redChannel, 30);
  ledcWrite(greenChannel, 30);
  ledcWrite(blueChannel, 30);

  digitalWrite(LED_RED_PIN, HIGH);
  digitalWrite(LED_GREEN_PIN, LOW);
}

// ===============================
// LOOP
// ===============================
void loop() {
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  last_capteur_value = analogRead(PRESSURE_PIN);

  if (isnan(temperature) || isnan(humidity)) {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Erreur DHT22");
    delay(500);
    return;
  }

  // LCD
  lcd.setCursor(0, 1);
  lcd.print("ADC:");
  lcd.print(last_capteur_value);
  lcd.print("     ");

  lcd.setCursor(0, 0);
  lcd.print("T:");
  lcd.print(temperature, 1);
  lcd.print("C H:");
  lcd.print(humidity, 1);
  lcd.print("%");

  // Bouton
  int currentButtonState = digitalRead(BUTTON_PIN);
  if (previousButtonState == HIGH && currentButtonState == LOW) {
    envoiAuto = !envoiAuto;
    digitalWrite(LED_RED_PIN, envoiAuto);
    digitalWrite(LED_GREEN_PIN, !envoiAuto);
  }
  previousButtonState = currentButtonState;

  // RGB selon pression
  if (last_capteur_value <= 819) {
    ledcWrite(redChannel, 0); ledcWrite(greenChannel, 255); ledcWrite(blueChannel, 0);
  } else if (last_capteur_value <= 1638) {
    ledcWrite(redChannel, 127); ledcWrite(greenChannel, 255); ledcWrite(blueChannel, 0);
  } else if (last_capteur_value <= 2457) {
    ledcWrite(redChannel, 255); ledcWrite(greenChannel, 255); ledcWrite(blueChannel, 0);
  } else if (last_capteur_value <= 3276) {
    ledcWrite(redChannel, 255); ledcWrite(greenChannel, 128); ledcWrite(blueChannel, 0);
  } else {
    ledcWrite(redChannel, 255); ledcWrite(greenChannel, 0); ledcWrite(blueChannel, 0);
  }

  // ===============================
  // SORTIE STREAMLIT (LA SEULE MODIF)
  // ===============================
  float deformation = last_capteur_value * 0.001; // calibration à faire

  Serial.print(temperature);
  Serial.print(";");
  Serial.print(humidity);
  Serial.print(";");
  Serial.print(last_capteur_value);
  Serial.print(";");
  Serial.print(deformation);
  Serial.println(";");

  delay(200);
}
