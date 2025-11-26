import { Routes } from '@angular/router';
import { AutoRegistrationComponent } from './components/auto-registration/auto-registration.component';
import { RecognitionComponent } from './components/recognition/recognition.component';

export const routes: Routes = [
  { path: '', redirectTo: '/auto-registration', pathMatch: 'full' },
  { path: 'auto-registration', component: AutoRegistrationComponent },
  { path: 'recognition', component: RecognitionComponent },
  { path: '**', redirectTo: '/auto-registration' }
];
