#define TRIG_PIN 9
#define ECHO_PIN 10

void setup() {
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  Serial.begin(9600);
}

void loop() {
  // Envia o pulso ultrassônico
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);

  digitalWrite(TRIG_PIN, LOW);

  // Mede o tempo do retorno do sinal
  unsigned long duracao = pulseIn(ECHO_PIN, HIGH, 30000UL);

  if (duracao == 0) {
    Serial.println(-1);
  } else {
    float distancia = duracao * 0.0343 / 2;

    Serial.println(distancia);
  }

  delay(50);
}
