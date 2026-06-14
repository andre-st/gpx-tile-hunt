#!/usr/bin/env ./local/bin/python

# Standard:
import glob
import argparse
from   argparse    import RawTextHelpFormatter
from   collections import Counter

# Third party:
import gpxpy
from   shapely.geometry import LineString, box
from   pyproj           import Transformer
import simplekml

# Own:
import config


# WGS84 <-> Web Mercator:
to_merc  = Transformer.from_crs( "EPSG:4326", "EPSG:3857", always_xy=True )
to_wgs84 = Transformer.from_crs( "EPSG:3857", "EPSG:4326", always_xy=True )


def get_user_args():
	parser = argparse.ArgumentParser(
		description = (
			"Gemerates a tiles mesh KML-file from given GPX routes to identify undiscovered areas more easily\n\n"
			"Author: https://github.com/andre-st/" 
		),
		epilog = (
			"Examples:\n"
			"  ./gpx2kml.py\n"
			"  ./gpx2kml.py --kml-file=routes.kml\n"
			"  ./gpx2kml.py ./routes/*tour_recorded*.gpx\n"
			"\n"
			"License:\n"
			"   MIT License"
		),
		formatter_class = RawTextHelpFormatter
	)
	parser.add_argument( "gpx_files",           help=f"load route from the given GPX file path, default: {config.DEFAULT_GPX_PATTERN}", nargs="*" )
	parser.add_argument( "-o", "--kml-file",    help=f"output KML file, default: {config.DEFAULT_KML_FILE}",               default=config.DEFAULT_KML_FILE )
	parser.add_argument( "-t", "--tile-size-m", help=f"tile size in square meters, default: {config.DEFAULT_TILE_SIZE_M}", default=config.DEFAULT_TILE_SIZE_M, type=int )
	args = parser.parse_args()
	
	if not args.gpx_files:
		args.gpx_files = glob.glob( config.DEFAULT_GPX_PATTERN )
	
	if not args.gpx_files:
		print( "[WARN] GPX files missing. Nothing to do. Try --help" )
	
	return args


def main():
	args = get_user_args()
	
	####################################################################
	#
	#  Read GPX files and collect visited tiles
	#
	
	visited_tiles = Counter()
	
	for i, gpx_file in enumerate( args.gpx_files ):
		
		print( f"Processing {gpx_file}" )
		
		with open( gpx_file, "r", encoding="utf-8" ) as f:
			gpx = gpxpy.parse( f )
		
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
					visited_tiles[ (tx,ty) ] += 1
	
	
	####################################################################
	#
	#  Create KML
	#
	
	kml = simplekml.Kml()
	
	# Semi-transparent colors for low and high visit frequency. 
	# Note: KML <Style> is used by Google My Maps but ignored by leaflet-omnivore.
	tile_color_hi                 = simplekml.Color.hex( config.TILE_COLOR_HI_RGB_HEX )
	tile_color_lo                 = simplekml.Color.hex( config.TILE_COLOR_LO_RGB_HEX )
	tile_style_hi                 = simplekml.Style()
	tile_style_lo                 = simplekml.Style()
	tile_style_hi.linestyle.width = 1
	tile_style_lo.linestyle.width = 1
	tile_style_hi.linestyle.color = tile_color_hi
	tile_style_lo.linestyle.color = tile_color_lo
	tile_style_hi.polystyle.color = simplekml.Color.changealphaint( int(config.TILE_OPACITY*255), tile_color_hi )
	tile_style_lo.polystyle.color = simplekml.Color.changealphaint( int(config.TILE_OPACITY*255), tile_color_lo )
	
	for (tx, ty), num_visits in visited_tiles.items():
		
		minx = tx   * args.tile_size_m
		miny = ty   * args.tile_size_m
		maxx = minx + args.tile_size_m
		maxy = miny + args.tile_size_m
		
		corners_merc = [   # in KML rects are polygons with 4 corners + closing point (same as first)
			(minx, miny),
			(maxx, miny),
			(maxx, maxy),
			(minx, maxy),
			(minx, miny) 
		]
		
		corners_wgs = [ to_wgs84.transform( x, y )         for x, y     in corners_merc ]
		corners_wgs = [ (round( lon, 6 ), round( lat, 6 )) for lon, lat in corners_wgs  ]  # less precision = smaller KML file
		pol         = kml.newpolygon( outerboundaryis=corners_wgs )
		pol.style   = tile_style_hi if num_visits >= config.NUM_VISITS_HI else tile_style_lo  # abs. N visits is well-known/beaten path
	
	
	kml.save( args.kml_file )
	
	print( f"{len(visited_tiles)} tiles written to {args.kml_file}" )



if __name__ == "__main__":
	main()

