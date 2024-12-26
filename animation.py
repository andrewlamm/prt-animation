import pygame
from pygame.locals import *
import csv
from collections import defaultdict
import random
import datetime
import requests
import pickle
import os
import sys

# ### DOWNTOWN DIMENSIONS
# COORD_TOP = 40.446656
# COORD_BOTTOM = 40.435827
# COORD_LEFT = -80.013743
# COORD_RIGHT = -79.995785

# MAP_FILENAME = 'maps/downtown.png'

# WIDTH = 1674 // 2
# HEIGHT = 1324 // 2

# ### DOWNTOWN LARGER DIMENSIONS
# COORD_TOP = 40.45171450062673
# COORD_BOTTOM = 40.42886548299837
# COORD_LEFT = -80.0176087448706
# COORD_RIGHT = -79.96510767200141

# MAP_FILENAME = 'maps/downtown_larger.png'

# WIDTH = 2132 // 2
# HEIGHT = 1226 // 2

### DOWNTOWN LARGER NO LABEL DIMENSIONS
COORD_TOP = 40.45067201331527
COORD_BOTTOM = 40.42964171974559
COORD_LEFT = -80.02358545397188
COORD_RIGHT = -79.96838954014908

MAP_FILENAME = 'maps/downtown_nolabel.png'

WIDTH = 2570 // 2
HEIGHT = 1294 // 2

# ### OAKLAND-SQ HILL DIMENSIONS
# COORD_TOP = 40.45584650286938
# COORD_BOTTOM = 40.42863259638758
# COORD_LEFT = -79.97622027045387
# COORD_RIGHT = -79.91762312752157

# MAP_FILENAME = 'maps/oakland_sqhill.png'

# WIDTH = 2154 // 2
# HEIGHT = 1318 // 2

COORD_WIDTH = COORD_RIGHT - COORD_LEFT
COORD_HEIGHT = COORD_TOP - COORD_BOTTOM

FPS = 300

TRIPS_FILTER = ["3"] # Only include trips on weekdays

START_TIME = '07:00:00'
END_TIME = '10:00:00'

def coord_to_pic(latitude, longitude):
  return ((longitude - COORD_LEFT) / COORD_WIDTH) * WIDTH, ((COORD_TOP - latitude) / COORD_HEIGHT) * HEIGHT

def parse_time(time):
  hours = int(time[:time.index(':')])
  rest = time[time.index(':'):]
  hours %= 24
  return datetime.datetime.strptime(f'{str(hours)}{rest}', '%H:%M:%S')

def time_string(time):
  return time.strftime('%H:%M:%S')

def color_is_dark(color):
  color = color[1:7] if color[0] == "#" else color
  r = int(color[0:2], 16) # hex of R
  g = int(color[2:4], 16) # hex of G
  b = int(color[4:6], 16) # hex of B
  uicolors = [r / 255, g / 255, b / 255]
  c = [color / 12.92 if color <= 0.03928 else ((color + 0.055) / 1.055) ** 2.4 for color in uicolors]
  L = (0.2126 * c[0]) + (0.7152 * c[1]) + (0.0722 * c[2])
  return L <= 0.179

override_cache = True if len(sys.argv) > 1 and sys.argv[1] == '--force' else False

print('Loading data...')
SEGMENTS = {}
if os.path.exists('cache/segments.pkl') and not override_cache:
  with open('cache/segments.pkl', 'rb') as file:
    SEGMENTS = pickle.load(file)
else:
  SEGMENTS_DICT = defaultdict(lambda: defaultdict(lambda: {}))
  with open('data/shapes.txt', 'r') as file:
    csv_reader = csv.reader(file)
    header = False
    for row in csv_reader:
      if not header:
        header = True
        continue

      shape_id = row[0]
      latitude = float(row[1])
      longitude = float(row[2])
      sequence = int(row[3])
      distance = float(row[4])

      SEGMENTS_DICT[shape_id][sequence] = {'coord': (latitude, longitude), 'distance': distance}
  for shape_id in SEGMENTS_DICT:
    SEGMENTS[shape_id] = list(map(lambda elm: elm[1], sorted(SEGMENTS_DICT[shape_id].items())))

  with open('cache/segments.pkl', 'wb') as file:
    pickle.dump(SEGMENTS, file)

STOPS = {}
if os.path.exists('cache/stops.pkl') and not override_cache:
  with open('cache/stops.pkl', 'rb') as file:
    STOPS = pickle.load(file)
else:
  with open('data/stops.txt', 'r') as file:
    csv_reader = csv.reader(file)
    header = False
    for row in csv_reader:
      if not header:
        header = True
        continue

      stop_id = row[0]
      latitude = float(row[4])
      longitude = float(row[5])

      STOPS[stop_id] = (latitude, longitude)

  with open('cache/stops.pkl', 'wb') as file:
    pickle.dump(STOPS, file)

TRIPS = {}
if os.path.exists('cache/trips.pkl') and not override_cache:
  with open('cache/trips.pkl', 'rb') as file:
    TRIPS = pickle.load(file)
else:
  with open('data/trips.txt', 'r') as file:
    csv_reader = csv.reader(file)
    header = False
    for row in csv_reader:
      if not header:
        header = True
        continue

      trip_id = int(row[0])
      route_id = row[1]
      service_id = row[2]
      shape_id = row[7]

      if service_id in TRIPS_FILTER:
        TRIPS[trip_id] = (route_id, shape_id)

  with open('cache/trips.pkl', 'wb') as file:
    pickle.dump(TRIPS, file)

STOP_TIMES = {}
if os.path.exists('cache/stop_times.pkl') and not override_cache:
  with open('cache/stop_times.pkl', 'rb') as file:
    STOP_TIMES = pickle.load(file)
else:
  STOP_TIMES_DICT = defaultdict(lambda: defaultdict(lambda: {}))
  with open('data/stop_times.txt', 'r') as file:
    csv_reader = csv.reader(file)
    header = False
    for row in csv_reader:
      if not header:
        header = True
        continue

      trip_id = int(row[0])
      arrival_time = parse_time(row[1])
      departure_time = parse_time(row[2])
      if arrival_time == departure_time:
        departure_time = departure_time + datetime.timedelta(seconds=1)
      stop_id = row[3]
      sequence = int(row[4])
      distance = float(row[8])

      STOP_TIMES_DICT[trip_id][sequence] = {'arrival_time': arrival_time,
                                            'departure_time': departure_time,
                                            'stop_id': stop_id,
                                            'distance': distance}
  STOP_TIMES = {}
  for trip_id in STOP_TIMES_DICT:
    STOP_TIMES[trip_id] = list(map(lambda elm: elm[1], sorted(STOP_TIMES_DICT[trip_id].items())))

  with open('cache/stop_times.pkl', 'wb') as file:
    pickle.dump(STOP_TIMES, file)

# for trip_id in STOP_TIMES:
#   if trip_id in TRIPS and TRIPS[trip_id][0] == '40':
#     print(f'{trip_id}: {time_string(STOP_TIMES[trip_id][0]["arrival_time"])}')

ROUTE_COLORS = {'1': '#3300cc', '11': '#ff4500', '12': '#cc00cc', '13': '#ff6666', '14': '#f4a460', '15': '#ff6633', '16': '#fa8072', '17': '#ff3300', '18': '#bc8f8f', '19L': '#00ff66', '2': '#ff33cc', '20': '#00cc00', '21': '#99cc00', '22': '#00ff00', '24': '#009900', '26': '#006666', '27': '#009999', '28X': '#b22222', '29': '#0066cc', '31': '#00cccc', '36': '#ff6699', '38': '#ff99cc', '39': '#ff7f50', '4': '#cc6666', '40': '#ff99ff', '41': '#0099cc', '43': '#ff9966', '44': '#ffcc00', '48': '#ff0066', '51': '#cc3300', '51L': '#3300ff', '52L': '#9966cc', '53': '#ff9999', '53L': '#ff9900', '54': '#ff1493', '55': '#999933', '56': '#ff0000', '57': '#cc0066', '58': '#00ff99', '59': '#6a5acd', '6': '#ffcc33', '60': '#999900', '61A': '#1e90ff', '61B': '#5f9ea0', '61C': '#00ffff', '61D': '#66cdaa', '64': '#cc6633', '65': '#cc3399', '67': '#00cc66', '69': '#c8c8c8', '7': '#336666', '71': '#666699', '71A': '#dc143c', '71B': '#ffa07a', '71C': '#f08080', '71D': '#cd5c5c', '74': '#ff33ff', '75': '#669933', '77': '#0099ff', '79': '#ff9933', '8': '#3cb371', '81': '#ff66cc', '82': '#ffd700', '83': '#00ff33', '86': '#0000ff', '87': '#ff69b4', '88': '#0066ff', '89': '#ccff00', '91': '#3366ff', '93': '#ba55d3', 'G2': '#008000', 'G3': '#7cfc00', 'G31': '#32cd32', 'O1': '#ff6600', 'O12': '#ff8c00', 'O5': '#ff7f50', 'P1': '#9900ff', 'P10': '#9932cc', 'P12': '#ff00ff', 'P13': '#cc33cc', 'P16': '#cc0000', 'P17': '#990033', 'P3': '#cc00ff', 'P67': '#993399', 'P68': '#ff0099', 'P69': '#ff66ff', 'P7': '#9933ff', 'P71': '#6666ff', 'P76': '#6600ff', 'P78': '#6633ff', 'Y1': '#ffff33', 'Y45': '#daa520', 'Y46': '#b87333', 'Y47': '#f6a600', 'Y49': '#ffff00', 'BLUE': '#0033ff', 'RED': '#990000', 'SLVR': '#6699ff', 'SWL': '#c8c8c8'}

# To update colors, insert key here and run this code
# routes = requests.get("https://truetime.rideprt.org/bustime/api/v3/getroutes?key=KEY&format=json").json()
# for routes in routes['bustime-response']['routes']:
#   ROUTE_COLORS[routes['rt']] = routes['rtclr']

TRIP_DATA = {}
for trip_id in TRIPS:
  TRIP_DATA[trip_id] = {'active': False,
                        'at_stop': False,
                        'distance_delta': 0.0,
                        'total_shape_length': 0.0,
                        'current_shape_index': 0, # index of the shape coord we are going to
                        'current_stop_index': 0, # index of the stop we are going to
                        'coord': None}

def update_trips():
  for trip_id in TRIP_DATA:
    if not TRIP_DATA[trip_id]['active']:
      if STOP_TIMES[trip_id][0]['arrival_time'] == currTime:
        TRIP_DATA[trip_id]['active'] = True
        TRIP_DATA[trip_id]['at_stop'] = True
        TRIP_DATA[trip_id]['coord'] = STOPS[STOP_TIMES[trip_id][0]['stop_id']]
    else:
      if STOP_TIMES[trip_id][TRIP_DATA[trip_id]['current_stop_index']]['arrival_time'] == currTime:
        # logic for arriving at stop
        TRIP_DATA[trip_id]['total_shape_length'] += TRIP_DATA[trip_id]['distance_delta']

        TRIP_DATA[trip_id]['at_stop'] = True
        # TRIP_DATA[trip_id]['coord'] = STOPS[STOP_TIMES[trip_id][TRIP_DATA[trip_id]['current_stop_index']]['stop_id']]
      elif STOP_TIMES[trip_id][TRIP_DATA[trip_id]['current_stop_index']]['departure_time'] == currTime:
        # logic for departing stop
        TRIP_DATA[trip_id]['at_stop'] = False
        TRIP_DATA[trip_id]['current_stop_index'] += 1

        if TRIP_DATA[trip_id]['current_stop_index'] >= len(STOP_TIMES[trip_id]):
          TRIP_DATA[trip_id]['active'] = False
        else:
          current_stop = STOP_TIMES[trip_id][TRIP_DATA[trip_id]['current_stop_index']]
          prev_stop = STOP_TIMES[trip_id][TRIP_DATA[trip_id]['current_stop_index'] - 1]

          total_distance = current_stop['distance'] - TRIP_DATA[trip_id]['total_shape_length']
          total_time = (current_stop['arrival_time'] - prev_stop['departure_time']).seconds

          TRIP_DATA[trip_id]['distance_delta'] = total_distance / total_time
      else:
        # logic for continuing on route
        TRIP_DATA[trip_id]['total_shape_length'] += TRIP_DATA[trip_id]['distance_delta']
        shape_id = TRIPS[trip_id][1]

        assert TRIP_DATA[trip_id]['current_shape_index'] + 1 <= len(SEGMENTS[shape_id])

        while TRIP_DATA[trip_id]['total_shape_length'] >= SEGMENTS[shape_id][TRIP_DATA[trip_id]['current_shape_index']]['distance']:
          TRIP_DATA[trip_id]['current_shape_index'] += 1

        shape_index = TRIP_DATA[trip_id]['current_shape_index']
        assert shape_index > 0 # make sure we can go back one segment

        segment_length = SEGMENTS[shape_id][shape_index]['distance'] - SEGMENTS[shape_id][shape_index - 1]['distance']
        current_segment_length = TRIP_DATA[trip_id]['total_shape_length'] - SEGMENTS[shape_id][shape_index - 1]['distance']
        ratio = current_segment_length / segment_length

        next_coord = SEGMENTS[shape_id][shape_index]['coord']
        prev_coord = SEGMENTS[shape_id][shape_index - 1]['coord']

        TRIP_DATA[trip_id]['coord'] = (prev_coord[0] + (next_coord[0] - prev_coord[0]) * ratio,
                                      prev_coord[1] + (next_coord[1] - prev_coord[1]) * ratio)

currTime = parse_time('00:00:00')
startTime = parse_time(START_TIME)
endTime = parse_time(END_TIME)

print("Initializing trips...")
startPrev = startTime - datetime.timedelta(seconds=1)
for trip_id in TRIP_DATA:
  for i in range(len(STOP_TIMES[trip_id])):
    if STOP_TIMES[trip_id][0]['arrival_time'] < startPrev and STOP_TIMES[trip_id][i]['arrival_time'] >= startPrev:
      TRIP_DATA[trip_id]['active'] = True
      TRIP_DATA[trip_id]['current_stop_index'] = i

      shape_id = TRIPS[trip_id][1]

      stop_index = TRIP_DATA[trip_id]['current_stop_index']
      stop = STOP_TIMES[trip_id][stop_index]
      prev_stop = STOP_TIMES[trip_id][stop_index - 1]
      stop_distance = stop['distance'] - prev_stop['distance']
      stop_time = (stop['arrival_time'] - prev_stop['departure_time']).seconds

      TRIP_DATA[trip_id]['distance_delta'] = stop_distance / stop_time

      time_passed = (startPrev - prev_stop['departure_time']).seconds
      TRIP_DATA[trip_id]['total_shape_length'] = prev_stop['distance'] + TRIP_DATA[trip_id]['distance_delta'] * time_passed

      for j in range(len(SEGMENTS[shape_id])):
        if SEGMENTS[TRIPS[trip_id][1]][j]['distance'] > TRIP_DATA[trip_id]['total_shape_length']:
          TRIP_DATA[trip_id]['current_shape_index'] = j
          break

      shape_index = TRIP_DATA[trip_id]['current_shape_index']
      segment_length = SEGMENTS[shape_id][shape_index]['distance'] - SEGMENTS[shape_id][shape_index - 1]['distance']
      current_segment_length = TRIP_DATA[trip_id]['total_shape_length'] - SEGMENTS[shape_id][shape_index - 1]['distance']
      ratio = current_segment_length / segment_length

      next_coord = SEGMENTS[shape_id][shape_index]['coord']
      prev_coord = SEGMENTS[shape_id][shape_index - 1]['coord']

      TRIP_DATA[trip_id]['coord'] = (prev_coord[0] + (next_coord[0] - prev_coord[0]) * ratio,
                                    prev_coord[1] + (next_coord[1] - prev_coord[1]) * ratio)

      break

currTime = startTime

print("Starting animation...")
pygame.init()
pygame.display.set_caption('PRT Animation')

screen = pygame.display.set_mode((WIDTH, HEIGHT))
img = pygame.image.load(MAP_FILENAME).convert()
img = pygame.transform.scale(img, (WIDTH, HEIGHT))
screen.blit(img, (0, 0))

# for shape_id in SEGMENTS:
#   color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
#   for i in range(1, len(SEGMENTS[shape_id])):
#     pygame.draw.line(screen, color,
#       coord_to_pic(SEGMENTS[shape_id][i - 1]['coord'][0], SEGMENTS[shape_id][i - 1]['coord'][1]),
#       coord_to_pic(SEGMENTS[shape_id][i]['coord'][0], SEGMENTS[shape_id][i]['coord'][1]), 2)

bigfont = pygame.font.SysFont('monospace', 28)
smallfont = pygame.font.SysFont('monospace', 9)

screenOn = True
started = False

while screenOn:
  pygame.time.Clock().tick(FPS)
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      screenOn = False
    elif event.type == pygame.MOUSEBUTTONUP or (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE):
      started = True

  screen.blit(img, (0, 0))
  text = bigfont.render(time_string(currTime), True, (0, 0, 0))
  text_surface = pygame.Surface(text.get_size())
  text_surface.set_alpha(162)
  text_surface.fill((255, 255, 255))
  text_surface.blit(text, (0, 0))
  # screen.blit(bigfont.render(time_string(currTime), True, (0, 0, 0)), (15, 15))
  screen.blit(text_surface, (15, 15))

  if currTime < endTime and started:
    # update locations of trips
    update_trips()

  # print(time_string(currTime))
  # for trip_id in TRIP_DATA:
  #   if TRIP_DATA[trip_id]['active']:
  #     print(f'{trip_id} ({TRIPS[trip_id][0]}): {coord_to_pic(TRIP_DATA[trip_id]["coord"][0], TRIP_DATA[trip_id]["coord"][1])} {TRIP_DATA[trip_id]["coord"]}')

  # draw trips
  for trip_id in TRIP_DATA:
    if TRIP_DATA[trip_id]['active']:
      coord = coord_to_pic(TRIP_DATA[trip_id]['coord'][0], TRIP_DATA[trip_id]['coord'][1])
      color = ROUTE_COLORS[TRIPS[trip_id][0]]
      pygame.draw.circle(screen, color, coord, 10)
      textcolor = (255, 255, 255) if color_is_dark(color) else (0, 0, 0)
      text = smallfont.render(TRIPS[trip_id][0], True, textcolor)
      screen.blit(text, text.get_rect(center=coord))

  if currTime < endTime and started:
    currTime += datetime.timedelta(seconds=1)

  pygame.display.flip()
