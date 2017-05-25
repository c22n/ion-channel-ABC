''' 
	Written by Aidan Daly, DPhil candidate, University of Oxford Department of Computer Science
	
	Part of a paper tutorial on ABC parameter estimation for the Hodgkin-Huxley 
	action potential model.
'''

'''
	Data digitized from the original 1952 Hodgkin-Huxley publication using 
	[http://plotdigitizer.sourceforge.net]
'''

# PLOT DATA ACCESSORS
	
''' 
	Potassium conductance recordings

	Returns x, y data from various traces of figure 3, as well as reported alpha/beta
	0=A, 1=B, ... , 10=K
'''
def fig3(plot=0):
	#Default: plot A
	x = [0.151969,0.346818,0.540928,0.708482,1.08186,1.48128,1.94706,2.77638,4.08767,6.38795,8.74094]
	y = [0.26035,0.469177,1.50235,3.15343,7.28047,11.3564,13.939,17.0936,19.2759,20.5448,21.0415]
	alpha, beta = 0.915,0.037
	
	if plot == 1:
		x = [0.143946,0.351982,0.546323,0.727155,1.08817,1.50074,1.96633,2.78252,4.14563,6.41981,8.79894]
		y = [0.7394,0.742386,1.5346,2.90553,6.38418,10.3899,13.2385,16.6184,19.0589,20.4598,20.8098]
		alpha, beta = 0.886,0.043
	if plot == 2:
		x = [0.166009,0.360627,0.564685,0.719812,1.10767,1.51457,1.98016,2.79612,4.14918,6.43957,8.78951,11.2179]
		y = [0.25768,0.719578,1.526,2.52307,4.97748,7.9296,10.6912,14.223,16.9205,18.3299,18.5922,18.3581]
		alpha, beta = 0.748,0.052
	if plot == 3:
		x = [0.181155,0.38587,0.570391,0.745402,1.12413,1.51208,1.9878,2.81355,4.15654,6.40831,8.79632,11.2246]
		y = [0.196537,0.276938,1.13222,1.71605,3.50426,5.87397,8.24492,11.7835,14.8643,15.865,17.1777,17.0957]
		alpha, beta = 0.61,0.057
	if plot == 4:
		x = [0.176417,0.390884,0.575647,0.750935,1.12043,1.52861,1.99489,2.8308,4.17366,6.44379,8.80331,11.2411]
		y = [0.514338,0.596152,1.18937,1.46748,2.6933,4.27401,6.32801,9.45034,12.7374,15.0535,15.5203,15.6734]
		alpha, beta = 0.524,0.064
	if plot == 5:
		x = [0.189592,0.384833,0.569941,0.754981,1.1346,1.54314,1.99071,2.81711,4.16031,6.42045,8.79916,11.2174,11.9878]
		y = [0.72418,0.499035,0.691458,0.959828,1.72454,2.86938,3.97679,6.72229,9.5129,12.0124,12.8047,13.0659,13.0006]
		alpha, beta = 0.419,0.069
	if plot == 6:
		x = [0.192635,0.387599,0.582563,0.758058,1.11856,1.53733,2.00485,2.8225,4.15637,6.4459,8.81437,11.2423,12.0029]
		y = [0.342299,0.420447,0.498595,0.538739,0.883313,1.49284,2.10304,3.73692,6.05714,8.39047,9.70601,10.0035,10.0517]
		alpha, beta = 0.310,0.075
	if plot == 7:
		x = [0.185443,0.351221,0.565688,0.750969,1.16043,1.56976,1.99835,2.84581,4.18023,6.45033,8.82848,11.2172,11.9973]
		y = [0.394772,0.397135,0.478621,0.481263,0.604742,0.885073,1.44017,2.51102,4.29465,6.64062,8.08621,8.59084,8.68039]
		alpha, beta = 0.241,0.071
	if plot == 8:
		x = [0.187172,0.362701,0.567555,0.77234,1.12336,1.5522,2.01038,2.81901,4.17345,6.46347,8.83215,11.2404,12.0104]
		y = [0.482695,0.485248,0.408227,0.411206,0.456312,0.742553,0.90922,1.80099,3.02071,4.93404,6.08851,6.64355,7.05475]
		alpha, beta = 0.192,0.072
	if plot == 9:
		x = [0.189039,0.345169,0.579174,0.774242,1.12527,1.58342,2.02211,2.84087,4.18601,6.43774,8.83581,11.2438,12.0042]
		y = [0.410034,0.301024,0.341214,0.306803,0.348568,0.539926,0.693985,1.11242,1.76018,2.75348,3.67468,4.37379,4.71736]
		alpha, beta = 0.15,0.072
	if plot == 10:
		x = [0.174412,0.320652,0.583981,0.749621,1.12018,1.51018,2.00731,2.84564,4.19074,6.41301,8.83059,11.2483,11.9989]
		y = [0.243338,0.253563,0.244784,0.284204,0.285513,0.306307,0.366316,0.456655,0.636163,0.954693,1.19624,1.38924,1.47927]
		alpha, beta = 0.095,0.096
	
	return x,y,alpha,beta

''' 
	Sodium conductance recordings

	Returns x, y data from various traces of figure 6, as well as reported alpha/beta
	0=A, 1=B, ... , 11=L
'''
def fig6(plot=0):
	x = [0.0580987,0.245054,0.45094,0.633994,1.0222,1.43846,1.89983,2.74176,4.09345,6.36252,8.75102]
	y = [12.7805,18.6875,17.6042,13.7258,6.93604,2.40338,2.06274,2.99761,2.40709,1.35057,0.235603]
	alpham,betam,alphah,betah = 7.0, 0.14, 0.0, 1.5
	
	if plot == 1:
		x = [0.0725912,0.222206,0.477492,0.644558,1.01639,1.44328,1.93142,2.76235,4.10341,6.39446,8.75577]
		y = [9.82182,17.438,17.6983,14.5564,7.51431,2.3621,1.09959,1.66155,1.66289,1.24847,0.0204379]
		alpham,betam,alphah,betah = 6.2, 0.02, 0.0, 1.5
	if plot == 2:
		x = [0.098071,0.275368,0.482326,0.665809,1.04863,1.45931,1.93624,2.76679,4.11881,6.40453,8.76071,11.2201]
		y = [7.17242,16.1389,17.7525,14.9343,8.21619,3.28084,1.0998,0.742808,0.959941,0.816022,0.34499,0.0861273]
		alpham,betam,alphah,betah = 5.15, -0.14, 0.0, 1.5
	if plot == 3:
		x = [0.113228,0.302092,0.492569,0.665771,1.04357,1.45955,1.94171,2.77714,4.12903,6.39864,8.76581,11.2143]
		y = [6.50252,17.31,18.4437,17.0782,11.3569,6.06888,3.38686,1.61475,1.50697,1.79769,1.64979,1.33562]
		alpham,betam,alphah,betah = 5.15, 0.13, 0.0, 1.19
	if plot == 4:
		x = [0.117334,0.288366,0.490452,0.669341,1.0645,1.49186,1.95753,2.79275,4.13903,6.40862,8.77049,11.2246]
		y = [3.96125,10.7829,13.7859,13.08,10.1074,6.1657,3.02903,0.738177,0.201635,0.435486,0.611963,0.569768]
		alpham,betam,alphah,betah = 3.82, 0.15, 0.0, 1.19
	if plot == 5:
		x = [0.128841,0.320947,0.512432,0.680998,1.06047,1.47729,1.97033,2.78921,4.1462,6.40479,8.79371,11.2262]
		y = [1.73966,7.06197,10.7908,11.4434,9.94467,6.74101,4.08379,1.63334,0.699943,0.554736,0.514217,0.691752]
		alpham,betam,alphah,betah = 2.82, 0.33, 0.0, 0.94
	if plot == 6:
		x = [0.118974,0.33179,0.517395,0.696884,1.07159,1.48386,1.97718,2.81246,4.14217,6.42784,8.7843,11.2275]
		y = [0.998115,3.66373,6.16998,6.96516,7.1645,6.23934,4.34843,2.23031,1.00207,0.699267,0.928484,0.726507]
		alpham,betam,alphah,betah = 2.03, 0.58, 0.0, 0.79
	if plot == 7:
		x = [0.142883,0.338875,0.523987,0.703605,1.07855,1.48558,1.96836,2.81476,4.16074,6.42473,8.77567,11.2299]
		y = [0.360193,1.71111,3.0081,4.14227,4.94265,4.49179,3.38578,1.88498,0.581813,0.383637,0.39941,0.628487]
		alpham,betam,alphah,betah = 1.36, 0.56, 0.0, 0.75
	if plot == 8:
		x = [0.154519,0.345768,0.531394,0.711548,1.09276,1.49472,1.96628,2.80646,4.17828,6.43139,8.79334,11.2421]
		y = [0.127692,0.752547,1.27854,1.78261,2.37298,2.46867,2.0583,1.34827,0.41422,0.363245,0.44327,0.478646]
		alpham,betam,alphah,betah = 0.95, 0.72, 0.02, 0.65
	if plot == 9:
		x = [0.157697,0.342809,0.533243,0.712711,1.09291,1.51647,1.98378,2.81412,4.17592,6.44512,8.78529,11.234]
		y = [0.0373728,0.296783,0.501803,0.65256,0.725643,0.754904,0.946865,0.766385,0.266481,0.118106,0.164825,0.199815]
		alpham,betam,alphah,betah = 0.81, 1.69, 0.03, 0.4
	if plot == 10:
		x = [0.165512,0.340365,0.530906,0.715739,1.09592,1.51387,1.97526,2.81663,4.16824,6.43753,8.78283,11.2531]
		y = [0.0401939,0.0841532,0.104374,0.113582,0.118433,0.113938,0.109416,0.102118,0.0894209,0.0812428,0.0730178,0.0698004]
		alpham,betam,alphah,betah = 0.66, 3.9, 0.05, 0.13
	if plot == 11:
		x = [0.172576,0.35788,0.564409,0.732633,1.10183,1.49274,2.02486,2.82295,4.18017,6.43878,8.80592,11.2438]
		y = [0.0129663,0.0405837,0.0488606,0.0453966,0.0451709,0.044932,0.0462875,0.0449594,0.0399283,0.038548,0.0354207,0.0372921]
		alpham,betam,alphah,betah = 0.51, 4.5, 0.06, 0.09
		
	return x,y,alpham,betam,alphah,betah
