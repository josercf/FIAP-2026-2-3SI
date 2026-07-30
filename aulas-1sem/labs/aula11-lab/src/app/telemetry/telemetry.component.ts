import { Component, OnInit, OnDestroy } from '@angular/core';
import { TelemetryService } from './telemetry.service';
import { Subscription } from 'rxjs';
import { map } from 'rxjs/operators';

@Component({
  selector: 'app-telemetry',
  template: `
    <div class="telemetry-dashboard">
      <h2>Painel de Telemetria - LogiTech</h2>
      <p>Caminhão ID: {{ truckId }}</p>
      <p>Velocidade Atual: <strong>{{ currentSpeed }} km/h</strong></p>
    </div>
  `
})
export class TelemetryComponent implements OnInit, OnDestroy {
  truckId = 'TRK-9988';
  currentSpeed = 0;
  private speedSubscription!: Subscription;

  constructor(private telemetryService: TelemetryService) {}

  ngOnInit(): void {
    this.speedSubscription = this.telemetryService.getSpeedData(this.truckId)
      .pipe(
        map(speed => speed > 90 ? 90 : speed) // Limitador de segurança via RxJS
      )
      .subscribe(speed => {
        this.currentSpeed = speed;
      });
  }

  ngOnDestroy(): void {
    // Evita memory leak ao destruir o componente
    if (this.speedSubscription) {
      this.speedSubscription.unsubscribe();
    }
  }
}
