import math

class ShipFilter:
    def __init__(self):
        self.zones = []

    def addZone(self,zoneData):
        self.zones.append(zoneData)

    def isInZone(self,shipLat,shipLon):
        for zone in self.zones:
            name, zoneLat, zoneLon, radius = zone

            zoneLat, zoneLon, shipLat, shipLon = map(math.radians, [zoneLat, zoneLon, shipLat, shipLon])

            dlat = shipLat - zoneLat
            dlon = shipLon - zoneLon

            a = math.sin(dlat / 2)**2 + math.cos(zoneLat) * math.cos(shipLat) * math.sin(dlon / 2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

            R = 6371
            distance = R * c
            
            if distance <= radius:
                return True
        
        return False