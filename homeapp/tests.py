from django.test import TestCase

# Create your tests here.

from django.http import JsonResponse
from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from .models import SmartThermostat
from .models import CarCharger



class SmartThermostatViewTest(TestCase):
    def setUp(self):
        # Create a SmartThermostat instance before each test
        self.thermostat = SmartThermostat.objects.create(
            temperature_in_room=20,
            set_temperature=22,
            humidity=45,
            mode='off'
        )

    @patch('homeapp.views.update_thermostat')  # Use the correct app name 'homeapp'
    def test_update_thermostat_with_stub(self, mock_stub):
        # Mock the return value of the stub
        mock_stub.return_value = JsonResponse({
            'status': 'updated',
            'new_temperature': 22,
            'new_mode': 'cool'
        })

        # Test the logic that uses the stub
        url = reverse('update_thermostat', args=[self.thermostat.id])  # Use the created thermostat's ID
        response = self.client.post(url, {'mode': 'cool'})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {
            'status': 'updated',
            'new_temperature': 22,
            'new_mode': 'cool'
        })


class SmartThermostatUnitTest(TestCase):
    def setUp(self):
        self.thermostat = SmartThermostat.objects.create(
            temperature_in_room=20,
            set_temperature=22,
            humidity=45,
            mode='off'
        )

    def test_update_thermostat_mode_unit(self):
        url = reverse('update_thermostat', args=[self.thermostat.id])
        response = self.client.post(url, {'mode': 'cool'})
        self.thermostat.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.thermostat.mode, 'cool')
        self.assertJSONEqual(response.content, {
            'status': 'updated',
            'new_temperature': self.thermostat.set_temperature,
            'new_mode': 'cool'
        })


class CarChargerUnitTests(TestCase):
    def setUp(self):
        self.car_charger = CarCharger.objects.create(
            car_battery_capacity=27,
            car_battery_charge=10,  
            max_power_output=60,
            power_consumption=50,  
            total_power_consumption=0 
        )

    def test_connect_to_car(self):
        # Tester kobling til bilen
        result = self.car_charger.connect_to_car()
        self.assertTrue(self.car_charger.is_connected_to_car)
        self.assertEqual(result, "Car is now connected.")

        # Tester forsøk på tilkobling når bilen allerede er tilkoblet
        result = self.car_charger.connect_to_car()
        self.assertEqual(result, "Car is already connected.")

    def test_disconnect_from_car(self):
        # kobler til bilen
        self.car_charger.connect_to_car()

        # Tester frakobling av bilen
        result = self.car_charger.disconnect_from_car()
        self.assertFalse(self.car_charger.is_connected_to_car)
        self.assertEqual(result, "Car is now disconnected.")

        # Tester forsøk på frakobling når bilen allerede er frakoblet
        result = self.car_charger.disconnect_from_car()
        self.assertEqual(result, "Car is already disconnected.")

    def test_start_charging(self):
        # Kobler til bilen først
        self.car_charger.connect_to_car()

        # Starter lading med en gyldig effekt
        result = self.car_charger.start_charging(power_rate=10)
        self.assertTrue(self.car_charger.is_charging)
        self.assertEqual(self.car_charger.power_consumption, 10)
        self.assertEqual(result, "Charging started at 10 kW.")

        # Starter lading med en effekt høyere enn maks kapasitet
        result = self.car_charger.start_charging(power_rate=25)
        self.assertEqual(result, "Power rate exceeds maximum output capacity.")

    def test_stop_charging(self):
        # Kobler til bilen og start lading først
        self.car_charger.connect_to_car()
        self.car_charger.start_charging(power_rate=10)

        # Stopper lading etter 60 minutter (1 time)
        result = self.car_charger.stop_charging(charging_minutes=60)
        self.assertFalse(self.car_charger.is_charging)
        self.assertEqual(self.car_charger.total_power_consumption, 10)  # 10 kW * 1 time
        self.assertEqual(result, "Charging stopped. Total power consumed: 10.00 kWh.")

        # Stopper lading når det ikke er en aktiv ladesesjon
        result = self.car_charger.stop_charging(charging_minutes=60)
        self.assertEqual(result, "No active charging session to stop.")

    def test_reset_power_consumption(self):
        # Setter totalt strømforbruk til en verdi
        self.car_charger.total_power_consumption = 50

        # Nullstiller strømforbruket
        result = self.car_charger.reset_power_consumption()
        self.assertEqual(self.car_charger.total_power_consumption, 0)
        self.assertEqual(result, "Total power consumption has been reset.")

    def test_calculate_estimated_charging_time_in_minutes(self):
        # Kobler til bilen og start lading først
        self.car_charger.connect_to_car()
        self.car_charger.start_charging(power_rate=10)

        # Estimerer ladetid fra nåværende lading til full kapasitet
        result = self.car_charger.calculate_estimated_charging_time_in_minutes()
        self.assertEqual(result, "Estimated charging time: 300.00 minutes.")

        # Setter batteriet til fulladet og verifiserer
        self.car_charger.car_battery_charge = 100
        self.car_charger.save()
        result = self.car_charger.calculate_estimated_charging_time_in_minutes()
        self.assertEqual(result, "Battery is already fully charged.")