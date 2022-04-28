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

double InTrueDistance;
double OutTrueDistance;
int NoiseThreshold = 150;
void setup()
{

  Serial.begin(9600);
  
  pinMode(9, OUTPUT);
  pinMode(10, OUTPUT);
  digitalWrite(9, LOW);
  digitalWrite(10, LOW);
  delay(500);
  
  Wire.begin();

  pinMode(9, INPUT);
  delay(150);
  Serial.println("00");
  InSensor.init(true);
  Serial.println("01");
  delay(100);
  InSensor.setAddress((uint8_t)22);
  Serial.println("02");



  pinMode(10, INPUT);
  delay(150);
  OutSensor.init(true);
  Serial.println("03");
  delay(100);
  OutSensor.setAddress((uint8_t)25);
  Serial.println("04");


  
  InSensor.setTimeout(500);
  OutSensor.setTimeout(500);
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

  // lower the return signal rate limit (default is 0.25 MCPS)
  OutSensor.setSignalRateLimit(0.1);
  // increase laser pulse periods (defaults are 14 and 10 PCLKs)
  OutSensor.setVcselPulsePeriod(VL53L0X::VcselPeriodPreRange, 18);
  OutSensor.setVcselPulsePeriod(VL53L0X::VcselPeriodFinalRange, 14);
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
  int inReads = 0;
  int outReads = 0;
  double inTotal = 0;
  double outTotal = 0; 
  while(time < endTime){
    Serial.println("Training");
    double inDistance = InSensor.readRangeSingleMillimeters();
    double outDistance = OutSensor.readRangeSingleMillimeters();
    if(inDistance < 8000 && inDistance > 50){ //Throw away bad values
      inTotal = inTotal + inDistance;
      inReads = inReads + 1;
    }
    if(outDistance < 8000 && outDistance > 50){ //Throw away bad values
      outTotal = outTotal + outDistance;
      outReads = outReads + 1;
    }
  time = millis();
  }
  InTrueDistance = inTotal / inReads;
  OutTrueDistance = outTotal / outReads;
  Serial.println("In True Distance: ");
  Serial.print(InTrueDistance);
  Serial.println("Out True Distance: ");
  Serial.print(OutTrueDistance);
  
}


double inMean[] = {InTrueDistance,InTrueDistance,InTrueDistance,InTrueDistance,InTrueDistance};
double outMean[] ={OutTrueDistance,OutTrueDistance,OutTrueDistance,OutTrueDistance,OutTrueDistance}; 
int inPos = 0;
int outPos = 0;

double getInMean(int dist){
   if(dist > 8000 || dist < 50){ // Throw away bad values
    return ((inMean[0] + inMean[1] + inMean[2] + inMean[3] + inMean[4]) / 5);
  }
  inMean[inPos] = dist;
  inPos += 1;
  inPos = inPos % 5;
  return ((inMean[0] + inMean[1] + inMean[2] + inMean[3] + inMean[4]) / 5);
  }
  

double getOutMean(double dist){
   if(dist > 8000 || dist < 50){ // Throw away bad values
    return ((outMean[0] + outMean[1] + outMean[2] + outMean[3] + outMean[4]) / 5);
  }
  outMean[outPos] = dist;
  outPos += 1;
  outPos = inPos % 5;
  return ((outMean[0] + outMean[1] + outMean[2] + outMean[3] + outMean[4]) / 5);
  }
  

int RoomOccupancy = 0; 

void loop()
{
  // On startup, train for the true distance
  if(Trained == false){
    Train();
    for(int i = 0; i < 5; i ++){ //Set the initial mean array to the true distance 
      inMean[i] = InTrueDistance;
      outMean[i] = OutTrueDistance;
      }
    for (int i = 0; i < 5; i++){ //For whatever reason, the first 5 reads mess things up. Doing them before checking path crossing fixes this. 
      double inDistance = InSensor.readRangeSingleMillimeters();
      inDistance = getInMean(inDistance);
      double outDistance = OutSensor.readRangeSingleMillimeters();
      outDistance = getOutMean(outDistance);
      }
  }
  
    double inDistance = InSensor.readRangeSingleMillimeters();  // Collect InSensor data
    double meanInDistance = getInMean(inDistance);
    double outDistance = OutSensor.readRangeSingleMillimeters();  // Collect InSensor data
    double meanOutDistance = getOutMean(outDistance);// Get the mean
   // Serial.print("In: ");
   // Serial.print(meanInDistance);
   // Serial.print(" Out: ");
   // Serial.print(meanOutDistance);

  boolean entering = false;
  boolean leaving = false;
  
  while((meanInDistance - InTrueDistance > NoiseThreshold) || (meanInDistance - InTrueDistance < (-1 * NoiseThreshold))){ 
    // If the difference between the mean and true distance is more than 150, the path has been crossed
    inDistance = InSensor.readRangeSingleMillimeters();  // Collect InSensor data
    meanInDistance = getInMean(inDistance);
    outDistance = OutSensor.readRangeSingleMillimeters();  // Collect InSensor data
    meanOutDistance = getOutMean(outDistance);// Get the mean
    if((meanOutDistance - OutTrueDistance > NoiseThreshold) || (meanOutDistance - OutTrueDistance < (-1 * NoiseThreshold))){
    Serial.println("Going Out");
    }    
    }
    
  while((meanOutDistance - OutTrueDistance > NoiseThreshold) || (meanOutDistance - OutTrueDistance < (-1 * NoiseThreshold))){ 
    inDistance = InSensor.readRangeSingleMillimeters();  // Collect InSensor data
    meanInDistance = getInMean(inDistance);
    outDistance = OutSensor.readRangeSingleMillimeters();  // Collect InSensor data
    meanOutDistance = getOutMean(outDistance);// Get the mean
    if((meanInDistance - InTrueDistance > NoiseThreshold) || (meanInDistance - InTrueDistance < (-1 * NoiseThreshold))){
      Serial.println("Going in");
    }
  }
    
    


  
  if (InSensor.timeoutOccurred()) { Serial.print(" TIMEOUT"); }
  //Serial.println();
}
