import json
import logging
import math
import sqlite3
import time


class ShipTracker:
    def __init__(self, track_limit:int, db_path:str, message_queue:any, vessel_queue:any):
        self.logger = logging.getLogger(__name__)

        self.vessels = {}
        self.max_tracked = track_limit

        self.zones = []

        self.message_queue = message_queue
        self.vessel_queue = vessel_queue

        self.__init_database(db_path)

    def __del__(self):
        self.db_conn.close()

    def __init_database(self, db_path:str):
        self.db_conn = sqlite3.connect(db_path)
        self.db_conn.row_factory = sqlite3.Row
        self.db_cur = self.db_conn.cursor()

        self.db_cur.execute("""
            CREATE TABLE IF NOT EXISTS vessels (
                mmsi TEXT PRIMARY KEY,
                imo TEXT,
                name TEXT,
                callsign TEXT,
                type INTEGER,
                bow INTEGER,
                stern INTEGER,
                port INTEGER,
                starboard INTEGER,
                first_sight INTEGER,
                last_sight INTEGER
            );""")
    
    def begin_processing(self):
        while True:
            msg = self.message_queue.get()

            if msg is None:
                continue

            try:
                data = json.loads(msg)
            except json.JSONDecodeError as e:
                self.logger.exception("Error decoding JSON", exc_info=e)
                continue

            self.update_vessel(data)

    def update_vessel(self, message:dict[str,any]):
        msg_type = message["msg_type"]
        mmsi = message["mmsi"]

        # Ship MMSI should be 9 or more digits. Under 9 means it's
        # probably a base station, navigation aid etc
        if len(str(mmsi)) < 9:
            self.logger.info(f"MMSI {str(mmsi)} is not a ship. Skip update.")
            return
        
        # If the first 3 values of MMSI are 111 this is a SAR aircraft
        if str(mmsi).startswith("111"):
            return
        
        # Only these 2 message types have static data
        has_static_data = msg_type == 5# or msg_type == 24

        # Make sure the database has a record of this ship.
        ship = self.__record_ship(message, has_static_data)

        # Filter out known static data keys to leave only dynamic data
        keyFilter = ["mmsi", "msg_type", "sentences", "callsign", "shipname",
                     "ship_type", "to_bow", "to_stern", "to_port", "to_starboard"]
        dynamic_data = {k: v for k, v in message.items() if k not in keyFilter}

        ship_prev = self.vessels.get(mmsi, {})
        zone_prev = ship_prev.get("zone", None)

        if "lat" in dynamic_data and "lon" in dynamic_data:
            ship["zone"] = self.check_zones(dynamic_data["lat"],dynamic_data["lon"])

        self.vessels[mmsi] = {**ship_prev, **ship, **dynamic_data, **{"ts": int(time.time())}}

        # Trim the tracked vessel list down if it's over the max size
        self.vessels = dict(sorted(self.vessels.items(), key=lambda item: item[1]['ts'], reverse=True)[:self.max_tracked])

        ship = self.vessels[mmsi]
        if self.vessel_queue is not None:
            if ship.get("zone", None) != zone_prev:
                self.vessel_queue.put(("zone",ship,zone_prev))

        self.logger.info(f"SHIP: {ship.get('name','Unknown')} {mmsi}, Zone: {ship.get('zone', 'None')}")
        self.vessel_queue.put(("update",ship))

    def add_zone(self, zone_data:list[dict[str,any]]):
        self.zones.append(zone_data)

    def check_zones(self, ship_lat:float, ship_lon:float):
        if len(self.zones) == 0:
            self.logger.info("Zone check request but no zones present")
            return None
        
        for zone in self.zones:
            name, zone_lat, zone_lon, radius = zone

            zone_lat, zone_lon, ship_lat, ship_lon = map(math.radians, [zone_lat, zone_lon, ship_lat, ship_lon])
            a:float = math.sin((ship_lat - zone_lat) / 2)**2 + math.cos(zone_lat) * math.cos(ship_lat) * math.sin((ship_lon - zone_lon) / 2)**2
            c:float = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

            EARTH_RADIUS:float = 6371
            distance:float = EARTH_RADIUS * c
            
            self.logger.info(f"Distance {distance} Radius {radius}")
            if distance <= radius:
                return name

        return None

    def __record_ship(self, message:dict[str,any], allow_update:bool):
        values = {
            'mmsi': message["mmsi"],
            'imo': message.get("imo", "0"),
            'name': message.get("shipname", "Unknown"),
            'callsign': message.get("callsign", "????"),
            'ship_type': message.get("ship_type", "-1"),
            'bow': message.get("to_bow", 0),
            'stern': message.get("to_stern", 0),
            'port': message.get("to_port", 0),
            'starboard': message.get("to_starboard", 0)
        }

        query = """
            INSERT INTO vessels (mmsi, imo, name, callsign, type, bow, stern, port, starboard, first_sight, last_sight)
            VALUES(:mmsi, :imo, :name, :callsign, :ship_type, :bow, :stern, :port, :starboard, strftime('%s', 'now'), strftime('%s', 'now'))
            ON CONFLICT(mmsi) DO UPDATE SET 
        """

        if allow_update:
            query += """
                    imo = excluded.imo,
                    name = excluded.name,
                    callsign = excluded.callsign,
                    type = excluded.type,
                    bow = excluded.bow,
                    stern = excluded.stern,
                    port = excluded.port,
                    starboard = excluded.starboard,
        """
            
        query += "last_sight = excluded.last_sight RETURNING *;"

        try:
            self.db_cur.execute(query, values)

            result = self.db_cur.fetchone()
            self.db_conn.commit()

            if result is not None:
                result = dict(result)

            return result
        except sqlite3.Error as e:
            self.logger.exception("SQLite error", exc_info=e)
            self.db_conn.rollback()

        return None