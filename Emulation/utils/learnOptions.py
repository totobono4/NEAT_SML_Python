empty = 0
mario = 1
enemy = 2
platform = 3
powerup = 4
block = 5
coin = 6

use_coins_in_fitness = False
use_score_in_fitness = False

activation = {
	mario:(True, empty, lambda tile: tile in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 66, 67, 68, 69, 70, 71]),

	enemy:(True, empty, lambda tile: tile in [144, 153, 154, 155, 160, 160, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 208, 209, 210, 211, 212 ,213, 214, 215, 218, 219, 220]),

	platform:(True, empty, lambda tile: tile in [128, 130, 142, 143, 231, 232, 234, 235, 236, 301, 304, 311, 319, 333, 334, 340, 352, 353, 354, 355, 356, 357, 358, 365, 366, 368, 369, 370, 371, 372, 373, 374 ,375, 376, 377, 378, 379 ,380, 381 ,382 ,383]),

	powerup:(False, empty, lambda tile: tile in [131, 132, 133, 134, 224, 229]),

	block:(False, platform, lambda tile: tile == 129),

	coin:(False, empty, lambda tile: tile in [244, 298])
}

minButtonPress = 0.85

reduceSize= 5