import browse_extract as b
import pylab as p
import pyfits

# name your favorite source

source = 'GX 301-2'
# get list of all obsids with source in FOV
obsids = b.heasarc('xtemaster',source,fields='obsid').obsid[1]

# pick first one and get proposal id (need to find in which AO observation occured)
our_obsid = obsids[0]
pid = our_obsid[:5]

# calculate ao number
ao = int(pid[:2])<90 and 'AO'+pid[0:1] or 'AO'+str(9+int(pid[1:2]))

# make path to lightcurve
path = ("ftp://legacy.gsfc.nasa.gov/xte/data/archive/"+
		ao+"/"+ "P"+pid+"/"+our_obsid+"/stdprod/xp"+
		our_obsid.replace('-','')+"_s2b.lc.gz")

# get mjd time + rate and error of source lightcurve in "B" energy range

time = pyfits.getval(path,'mjdrefi',1)+pyfits.getval(path,'mjdreff',1)+\
	   pyfits.getdata(path,1).field('time')/86400.
rate = pyfits.getdata(path,1).field('rate')
err  = pyfits.getdata(path,1).field('error')

p.title('RXTE PCA lightcurve for '+ source+',\n data from observation '+our_obsid)
p.errorbar(time,rate,err,ls='steps-mid',c='k')
p.xlabel('Time, MJD')
p.ylabel('RXTE PCA rate, cts/s')
p.show()


