/*
 * Square definitions
 * Created by thearst3rd on 8/6/2020
 */

#pragma once

#include <stdint.h>

// The square struct. These uint8_t's will be in range 1-8
typedef struct
{
	uint8_t file;
	uint8_t rank;
} sq;

#define SQ_INVALID ((sq) {-1, -1})

// Create a square from two ints, i.e. 5, 4
sq sqI(uint8_t file, uint8_t rank);
// Create a square from a SAN square, i.e. "e4"
sq sqS(const char *str);

// Convert square to and from an index 0-63 (0 is a1, 63 is h8, +1 moves across a rank)
sq sqIndex(uint8_t index);
uint8_t sqGetIndex(sq s);

// Gets the SAN string representing the given square. Does not need to be freed
const char *sqGetStr(sq s);

// Returns 1 if the square is a dark colored square, 0 if light
uint8_t sqIsDark(sq s);

// Compares two squares, returns true if equal and false otherwise
uint8_t sqEq(sq s1, sq s2);
