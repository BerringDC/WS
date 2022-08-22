import pandas as pd
import serial
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class WSException(Exception):
    pass

class WS(object):
    def __init__(self, portID):
        self.s = None
        self.portID = portID
        self.autoSession = True
        self.dfmwv = pd.DataFrame()
        self.dfmda = pd.DataFrame()
        self.df_total = pd.DataFrame()
        self.line = []
        self.latitude = None
        self.longitude = None
        self.datetime = None
        self.SOG = None
        self.COG_True = None
        self.COG_Magnetic = None

        try:
            self.s = serial.Serial(self.portID, 4800, timeout=None)

        except (Exception):
            pass

    def _ensureConnectionStatus(self):
        if (self.s == None or self.s.isOpen() == False):
            raise WSException()

    def store_csv(self, path):
        self._ensureConnectionStatus()
        if len(self.dfmda) != 0:
            if os.path.isfile(path + 'weather_station_MDA.csv'):
                self.dfmda.to_csv(path + 'weather_station_MDA.csv', index=False, header=False, mode='a')
            else:
                self.dfmda.to_csv(path + 'weather_station_MDA.csv', index=False, header=True)
        if len(self.dfmwv) != 0:
            if os.path.isfile(path + 'weather_station_MWV.csv'):
                self.dfmwv.to_csv(path + 'weather_station_MWV.csv', index=False, header=False, mode='a')
            else:
                self.dfmwv.to_csv(path + 'weather_station_MWV.csv', index=False, header=True)
    
    def store_all_csv(self, path):
        self._ensureConnectionStatus()
        if len(self.dfmda) != 0:
            mda = self.dfmda[['datetime', 'latitude', 'longitude', 'pressure', 'air_temperature', 'relative_humidity', 'absolute_humidity',
                                                     'dew_point', 'wind_direction', 'wind_speed', 'SOG', 'COG_T', 'COG_M']]
            
            mda['ti'] = pd.to_datetime(mda['datetime'], format='%y%m%d%H%M%S')
            mda['latitude'], mda['longitude'] =  pd.to_numeric(mda['latitude'], 'coerce'), pd.to_numeric(mda['longitude'], 'coerce')
            mda['pressure'] = pd.to_numeric(mda['pressure'], 'coerce')
            mda['SOG'] = pd.to_numeric(mda['SOG'], 'coerce')
            mda['COG_T'] = pd.to_numeric(mda['COG_T'], 'coerce')
            mda['COG_M'] = pd.to_numeric(mda['COG_M'], 'coerce')
            mda['air_temperature'] = pd.to_numeric(mda['air_temperature'], 'coerce')
            mda['relative_humidity'] = pd.to_numeric(mda['relative_humidity'], 'coerce')
            mda['dew_point'] = pd.to_numeric(mda['dew_point'], 'coerce')
            mda['wind_direction'] = pd.to_numeric(mda['wind_direction'], 'coerce')
            mda['wind_speed'] = pd.to_numeric(mda['wind_speed'], 'coerce')
            mda.set_index('ti', inplace=True)
            mda = mda.resample('1T').median().reset_index()
            mda['latitude'] = round(mda['latitude'], 6)
            mda['longitude'] = round(mda['longitude'], 6)
            mda['pressure'] = round(mda['pressure'], 4)
            mda['SOG'] = round(mda['SOG'], 1)
            mda['COG_T'] = round(mda['COG_T'], 1)
            mda['COG_M'] = round(mda['COG_M'], 1)
            mda['air_temperature'] = round(mda['air_temperature'], 1)
            mda['wind_direction'] = round(mda['wind_direction'], 1)
            mda['wind_speed'] = round(mda['wind_speed'], 1)
            mda = mda.reset_index()
            mda['datetime'] = mda['ti']
            mda.loc[:, 'id'] = self.dfmda.iloc[0]['id']
            mda = mda.iloc[:-1]
            if os.path.isfile(path + 'weather_station_MDA_mean.csv'):
                mda.to_csv(path + 'weather_station_MDA_mean.csv', index=None, columns=['id', 'datetime', 'latitude', 'longitude', 'pressure', 'air_temperature', 'relative_humidity', 'absolute_humidity',
                                                 'dew_point', 'wind_direction', 'wind_speed', 'SOG', 'COG_T', 'COG_M'], header=False, mode='a')
            else:
                mda.to_csv(path + 'weather_station_MDA_mean.csv', index=None, columns=['id', 'datetime', 'latitude', 'longitude', 'pressure', 'air_temperature', 'relative_humidity', 'absolute_humidity',
                                                 'dew_point', 'wind_direction', 'wind_speed', 'SOG', 'COG_T', 'COG_M'], header=True)
            self.dfmda = pd.DataFrame()

    def get_splitted_line(self):
        self._ensureConnectionStatus()
        try:
            self.line = self.s.readline().decode('utf-8').strip().split(',')
        except:
            print("Unicode error: waiting till it finds WS data...\n")
            self.get_splitted_line()

    def length(self):
        self._ensureConnectionStatus()
        return len(self.line)

    def id(self):
        self._ensureConnectionStatus()
        return self.line[0]

    def close(self):
        self._ensureConnectionStatus()
        if self.s != None:
            self.s.close()
            self.s = None

    def add_df(self):
        self._ensureConnectionStatus() 
        self.get_splitted_line()
        
        if self.id() == '$GPRMC' and self.length() == 13:
            self.line = [e.replace('\x00', '') for e in self.line]
            ids, time, state, latitude, latd, longitude, lond, _, _, date, _, _, _ = self.line            
            day = date[:2]
            month = date[2:4]
            year = date[4:]
            
            date = year + month + day

            time = str(int(float(time)))
            time = (6 - len(time)) * '0' + time

            self.datetime = date + time
            
            latitude, longitude = float(latitude), float(longitude)

            self.latitude = round(int(latitude / 100) + (latitude / 100 % 1) * 100 / 60, 6) if latd == 'N' else -round(
                int(latitude / 100) + (latitude / 100 % 1) * 100 / 60, 6)
            self.longitude = round(int(longitude / 100) + (longitude / 100 % 1) * 100 / 60, 6) if lond == 'E' else -round(
                int(longitude / 100) + (longitude / 100 % 1) * 100 / 60, 6)
        
        elif self.id() == '$GPZDA' and self.length() == 7:
            self.line = [e.replace('\x00', '') for e in self.line]
            ids, time, day, month, year, local_hour, local_minute = self.line
            month = (2 - len(month)) * '0' + month
            day = (2 - len(day)) * '0' + day
            date = year[-2:] + month + day

            time = str(int(float(time)))
            time = (6 - len(time)) * '0' + time

            self.datetime = date + time
            #print('Datetime: ', self.datetime)
        
        elif self.id() == '$GPVTG' and self.length() == 10:
            self.line = [e.replace('\x00', '') for e in self.line]
            ids, cogT, T, cogM, M, speed_og1, knots, speed_og2, kmh, mode = self.line
            self.COG_True = cogT
            self.COG_Magnetic = cogM
            self.SOG = round(float(speed_og2)/3.6, 1)

        elif self.id() == '$GPGGA' and self.length() == 15:
            self.line = [e.replace('\x00', '') for e in self.line]
            ids, time, latitude, latd, longitude, lond, quality, nsat, hdop, altitude, units, geoidal, _, _, _ = self.line
            latitude, longitude = float(latitude), float(longitude)

            self.latitude = round(int(latitude / 100) + (latitude / 100 % 1) * 100 / 60, 6) if latd == 'N' else -round(
                int(latitude / 100) + (latitude / 100 % 1) * 100 / 60, 6)
            self.longitude = round(int(longitude / 100) + (longitude / 100 % 1) * 100 / 60, 6) if lond == 'E' else -round(
                int(longitude / 100) + (longitude / 100 % 1) * 100 / 60, 6)
            
            #print('Latitude and longitude: ', self.latitude, ',', self.longitude)

        elif self.length() == 21 and self.id() == '$WIMDA':
            self.line = [e.replace('\x00', '') for e in self.line]
            ids, _, _, pressure, _, air_temp, _, _, _, rel_hum, abs_hum, dew, _, wd, _, _, _, wind_speed, _, _, _ = self.line
            #print('Air temperature: ',air_temp, '\nPressure: ', pressure, '\nWind: ', wind_speed)

            if self.datetime is not None and self.latitude is not None and self.longitude is not None:
                self.dfmda = self.dfmda.append(pd.DataFrame([[ids, self.datetime, self.latitude, self.longitude, pressure, air_temp, rel_hum, abs_hum, dew, wd, wind_speed, self.SOG, self.COG_True, self.COG_Magnetic]],
                                        columns=['id', 'datetime', 'latitude', 'longitude', 'pressure', 'air_temperature', 'relative_humidity', 'absolute_humidity',
                                                 'dew_point', 'wind_direction', 'wind_speed', 'SOG', 'COG_T', 'COG_M']), ignore_index=True)

    def print_line(self):
        self._ensureConnectionStatus()
        return self.line

    def reset_df(self):
        self.df_total = pd.DataFrame()
