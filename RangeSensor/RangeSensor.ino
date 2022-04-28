#include <Wire.h>
#include <VL53L0X.h>

VL53L0X InSensor;
VL53L0X OutSensor;



// Uncomment this line to use long range mode. This
// increases the sensitivity of the sensor and extends its
// potential range, but increases the likelihood of getting
// an inaccurate reading because of reflections from objects
// other than the intended target. It works best in dark
// conditions.

#define LONG_RANGE


// Uncomment ONE of these two lines to get
// - higher speed at the cost of lower accuracy OR
// - higher accuracy at the cost of lower speed

//#define HIGH_SPEED
//#define HIGH_ACCURACY

double TrueDistance;
int NoiseThreshold = 150;
void setup()
{
  Serial.begin(9600);
  Wire.begin();

  InSensor.setTimeout(500);
  if (!InSensor.init())
  {
    Serial.println("Failed to detect and initialize InSensor!");
    while (1) {}
  }

#if defined LONG_RANGE
  // lower the return signal rate limit (default is 0.25 MCPS)
  InSensor.setSignalRateLimit(0.1);
  // increase laser pulse periods (defaults are 14 and 10 PCLKs)
  InSensor.setVcselPulsePeriod(VL53L0X::VcselPeriodPreRange, 18);
  InSensor.setVcselPulsePeriod(VL53L0X::VcselPeriodFinalRange, 14);
#endif

#if defined HIGH_SPEED
  // reduce timing budget to 20 ms (default is about 33 ms)
  InSensor.setMeasurementTimingBudget(20000);
#elif defined HIGH_ACCURACY
  // increase timing budget to 200 ms
  InSensor.setMeasurementTimingBudget(200000);
#endif
}


// About 27 readings per second when set with LONG_RANGE, accurate up to about 2 meters 
// take 5 readings and take median ?


boolean Trained = false;
double Train(){
  // Calculate True Distance:
  Trained = true;
  delay(5000);
  int time = millis();
  int endTime = time + 1000;
  int reads = 0;
  int total = 0;
  while(time < endTime){
    Serial.println("Training");
    double distance = InSensor.readRangeSingleMillimeters();
    if(distance < 8000 && distance > 50){ //Throw away bad values
      total = total + distance;
      reads = reads + 1;
    }
  time = millis();
  }
  TrueDistance = total / reads;
  Serial.println("True Distance: ");
  Serial.print(TrueDistance);
  return(TrueDistance);
}


int mean[] = {TrueDistance,TrueDistance,TrueDistance,TrueDistance,TrueDistance};
int pos = 0;
double getMean(int dist){
  if(dist > 8000 || dist < 50){ // Throw away bad values
    return ((mean[0] + mean[1] + mean[2] + mean[3] + mean[4]) / 5);
  }
  mean[pos] = dist;
  pos += 1;
  pos = pos % 5;
  return ((mean[0] + mean[1] + mean[2] + mean[3] + mean[4]) / 5);
  }

int RoomOccupancy = 0; 
void loop()
{
  // On startup, train for the true distance
  if(Trained == false){
    TrueDistance = Train();
    for(int i = 0; i < 5; i ++){ //Set the initial mean array to the true distance 
      mean[i] = TrueDistance;}
      
    for (int i = 0; i < 5; i++){ //For whatever reason, the first 5 reads mess things up. Doing them before checking path crossing fixes this. 
      double distance = InSensor.readRangeSingleMillimeters();
      distance = getMean(distance);}
  }
  
    double distance = InSensor.readRangeSingleMillimeters();  // Collect InSensor data
    double meanDistance = getMean(distance);                // Get the mean
    //Serial.print(meanDistance);
    //Serial.print(" TRUE: ");
    //Serial.print(TrueDistance);

  boolean entering = false;
  boolean leaving = false;
  if((meanDistance - TrueDistance > NoiseThreshold) || (meanDistance - TrueDistance < (-1 * NoiseThreshold))){ 
    // If the difference between the mean and true distance is more than 150, the path has been crossed
    Serial.print("Path Crossed");
    // entering = (InSensorCrossed > OutSensorCrossed)
    if(entering){
      RoomOccupancy += 1;
    }
    if(leaving){
      if(RoomOccupancy > 0)
        RoomOccupancy -= 1;
    }
    if(RoomOccupancy == 0){
      Serial.print("empty");
    }
    if(RoomOccupancy > 0){
      Serial.print("Occupied");
    }
  }

  
  if (InSensor.timeoutOccurred()) { Serial.print(" TIMEOUT"); }
  Serial.println();
}
