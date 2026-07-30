import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class TelemetryService {
  constructor() { }

  /**
   * Retorna um Observable que emite a velocidade atualizada de um caminhão a cada 2 segundos.
   */
  getSpeedData(truckId: string): Observable<number> {
    return new Observable(subscriber => {
      console.log(`[TelemetryService] Iniciando monitoramento para ${truckId}`);
      
      const intervalId = setInterval(() => {
        const speed = Math.floor(Math.random() * 40) + 60; // 60 a 100 km/h
        subscriber.next(speed);
      }, 2000);

      // Função de Cleanup ao fazer o unsubscribe
      return () => {
        console.log(`[TelemetryService] Parando monitoramento para ${truckId}`);
        clearInterval(intervalId);
      };
    });
  }
}
