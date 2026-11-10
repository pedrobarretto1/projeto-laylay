#pragma once
// Perfil elétrico do corpo: zero desliga; o piso vale só para tração ativa.
#ifndef LAYLAY_PWM_MINIMO_MOTOR
#define LAYLAY_PWM_MINIMO_MOTOR 0
#endif
#ifndef LAYLAY_PWM_MAXIMO_MOTOR
#define LAYLAY_PWM_MAXIMO_MOTOR 255
#endif
static_assert(LAYLAY_PWM_MINIMO_MOTOR >= 0 && LAYLAY_PWM_MAXIMO_MOTOR >= 1
              && LAYLAY_PWM_MINIMO_MOTOR <= LAYLAY_PWM_MAXIMO_MOTOR
              && LAYLAY_PWM_MAXIMO_MOTOR <= 255, "Faixa PWM do motor invalida");
int ajustarPwmMotor(int valor) {
  if (!valor) return 0;
  int magnitude = valor < 0 ? -valor : valor;
  magnitude = max(int(LAYLAY_PWM_MINIMO_MOTOR), min(int(LAYLAY_PWM_MAXIMO_MOTOR), magnitude));
  return valor < 0 ? -magnitude : magnitude;
}
bool pwmMotorNoPerfil(int valor) { return valor == ajustarPwmMotor(valor); }
