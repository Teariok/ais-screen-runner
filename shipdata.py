import sqlite3
import os
import time

class ShipData:
    def __init__(self,dbName,imgDir,maxDynSize):
        self.imgDir = imgDir
        self.dynamicData = {}
        self.maxDynSize = maxDynSize

        if not os.path.exists(imgDir):
            os.mkdir(imgDir)

        self.conn = sqlite3.connect(dbName)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()

    def initTables(self):
        self.cur.execute("""
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

    def updateStaticShipData(self,data,canUpdate):
        values = {
            'mmsi': data["mmsi"],
            'imo': data.get("imo", "0"),
            'name': data.get("shipname", "Unknown"),
            'callsign': data.get("callsign", "????"),
            'ship_type': data.get("ship_type", "-1"),
            'bow': data.get("to_bow", 0),
            'stern': data.get("to_stern", 0),
            'port': data.get("to_port", 0),
            'starboard': data.get("to_starboard", 0)
        }

        query = """
            INSERT INTO vessels (mmsi, imo, name, callsign, type, bow, stern, port, starboard, first_sight, last_sight)
            VALUES(:mmsi, :imo, :name, :callsign, :ship_type, :bow, :stern, :port, :starboard, strftime('%s', 'now'), strftime('%s', 'now'))
            ON CONFLICT(mmsi) DO UPDATE SET 
        """

        if canUpdate:
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
            self.cur.execute(query, values)

            result = self.cur.fetchone()
            self.conn.commit()

            if result is not None:
                result = dict(result)
                result["dynamic"] = self.dynamicData.get(data["mmsi"], {})

            return result
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            self.conn.rollback()

        return None

    def updateShipDynamicData(self, message):
        keyFilter = ["mmsi", "msg_type", "sentences", "callsign", "shipname", "ship_type", "to_bow", "to_stern", "to_port", "to_starboard"]
        data = {k: v for k, v in message.items() if k not in keyFilter}

        shipData = self.dynamicData.get(message["mmsi"], {})
        self.dynamicData[message["mmsi"]] = {**shipData, **data, **{"ts": int(time.time())}}

        # Trim the dynamic data down if it's over the max size
        self.dynamicData = dict(sorted(self.dynamicData.items(), key=lambda item: item[1]['ts'], reverse=True)[:self.maxDynSize])

    def getLastKnownPosition(self, mmsi):
        if mmsi in self.dynamicData:
            ship = self.dynamicData[mmsi]

            if "lat" in ship and "lon" in ship:
                return (ship["lat"],ship["lon"])
            
        return None

    def getShipInfo(self, mmsi):
        try:
            self.cur.execute("SELECT * FROM vessels WHERE mmsi=:mmsi", {'mmsi': mmsi})
            return self.cur.fetchone()
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
        
        return None