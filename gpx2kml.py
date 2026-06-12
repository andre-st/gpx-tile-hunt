#!/usr/bin/env ./local/bin/python

# Standard:
import argparse
from   argparse import RawTextHelpFormatter
import glob

# Third party:
import gpxpy
from   shapely.geometry import LineString, box
from   pyproj           import Transformer
import simplekml

# Own:


# Static program configuration:
DEFAULT_GPX_PATTERN = "./routes/*.gpx"
DEFAULT_KML_FILE    = "routes.kml"
DEFAULT_TILE_SIZE_M = 1500

# WGS84 <-> Web Mercator:
to_merc  = Transformer.from_crs( "EPSG:4326", "EPSG:3857", always_xy=True )
to_wgs84 = Transformer.from_crs( "EPSG:3857", "EPSG:4326", always_xy=True )


def get_user_args():
	parser = argparse.ArgumentParser(
		description = (
			"Gemerates a tiles mesh KML file from given GPX routes to identify undiscovered areas more easily\n\n"
			"Author: https://github.com/andre-st/" 
		),
		epilog = (
			"Examples:\n"
			"  ./gpx2kml.py\n"
			"  ./gpx2kml.py --kml-file=routes.kml\n"
			"  ./gpx2kml.py --kml-file=routes.kml ./routes/*tour_recorded*.gpx\n"
			"\n"
			"License:\n"
			"   MIT License"
		),
		formatter_class = RawTextHelpFormatter
	)
	parser.add_argument( "gpx_files",           help=f"load route from the given GPX file path, default: {DEFAULT_GPX_PATTERN}", nargs="*" )
	parser.add_argument( "-o", "--kml-file",    help=f"output KML file, default: {DEFAULT_KML_FILE}",               default=DEFAULT_KML_FILE )
	parser.add_argument( "-t", "--tile-size-m", help=f"tile size in square meters, default: {DEFAULT_TILE_SIZE_M}", default=DEFAULT_TILE_SIZE_M, type=int )
	args = parser.parse_args()
	
	if not args.gpx_files:
		args.gpx_files = glob.glob( DEFAULT_GPX_PATTERN )
	
	if not args.gpx_files:
		print( "[WARN] GPX files missing. Nothing to do. Try --help" )
	
	return args


def main():
	args = get_user_args()
	
	####################################################################
	#
	#  Read GPX files and collect occupied tiles
	#
	
	occupied_tiles = set()
	
	for i, gpx_file in enumerate( args.gpx_files ):
		print( f"Processing {gpx_file}" )
		
		with open( gpx_file, "r", encoding="utf-8" ) as f:
			gpx = gpxpy.parse(f)
		
		coords = []
		
		# Tracks and routes:
		for track in gpx.tracks:
			for segment in track.segments:
				for p in segment.points:
					coords.append( (p.longitude, p.latitude) )
		
		for route in gpx.routes:
			for p in route.points:
				coords.append( (p.longitude, p.latitude) )
		
		if len( coords ) < 2:
			continue
		
		# Convert route to projected coordinates:
		merc_coords = [ to_merc.transform( lon, lat ) for lon, lat in coords ]
		
		line = LineString( merc_coords )
		
		minx, miny, maxx, maxy = line.bounds
		
		tx0 = int( minx // args.tile_size_m )
		ty0 = int( miny // args.tile_size_m )
		tx1 = int( maxx // args.tile_size_m )
		ty1 = int( maxy // args.tile_size_m )
		
		for tx in range( tx0, tx1 + 1 ):
			for ty in range( ty0, ty1 + 1 ):
				
				tile_poly = box(
					tx       * args.tile_size_m,
					ty       * args.tile_size_m,
					(tx + 1) * args.tile_size_m,
					(ty + 1) * args.tile_size_m
				)
				
				if line.intersects( tile_poly ):
					occupied_tiles.add( (tx,ty) )
	
	
	####################################################################
	#
	#  Create KML
	#
	
	kml = simplekml.Kml()
	
	for tx, ty in occupied_tiles:
		
		minx = tx   * args.tile_size_m
		miny = ty   * args.tile_size_m
		maxx = minx + args.tile_size_m
		maxy = miny + args.tile_size_m
		
		corners_merc = [
			(minx, miny),
			(maxx, miny),
			(maxx, maxy),
			(minx, maxy),
			(minx, miny),
		]
		
		corners_wgs = [ to_wgs84.transform( x, y  )for x, y in corners_merc ]
		
		pol = kml.newpolygon( outerboundaryis=corners_wgs )
		
		# Semi-transparent red
		pol.style.polystyle.color = simplekml.Color.changealphaint( 100, simplekml.Color.red )
		pol.style.linestyle.color = simplekml.Color.red
		pol.style.linestyle.width = 1
	
	
	kml.save( args.kml_file )
	
	print( f"{len(occupied_tiles)} tiles written to {args.kml_file}" )



if __name__ == "__main__":
	main()

