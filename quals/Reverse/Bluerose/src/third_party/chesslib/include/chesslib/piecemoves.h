/*
 * Definitions for how pieces move
 * I would want this to be in move.h but I want to avoid circular dependancies...
 * Created by thearst3rd on 9/15/2020
 */

#pragma once

#include "chesslib/board.h"
#include "chesslib/movelist.h"

// Returns a list for a generic piece type

// Leapers can leap to a square with the given offsets
// dirs is an array of tuples that define all offests to where the leaper can move
// For example: the knights array would be:
// 		dirs = {{1, 2}, {2, 1}, {2, -1}, {1, -2}, {-1, -2}, {-2, -1}, {-2, 1}, {-1, 2}}
// 		numDirs = 8
moveList *pmLeaperMoveList(board *b, sq s, pieceType pt, int8_t dirs[][2], size_t numDirs);
// A rider is a leaper that can keep moving in a fixed direction any number of times until it hits something
moveList *pmRiderMoveList(board *b, sq s, pieceType pt, int8_t dirs[][2], size_t numDirs);

// Each of these functions return a moveList of _potential_ moves, but they might leave the current player in check
moveList *pmGetPawnMoves(board *b, sq s);
moveList *pmGetKnightMoves(board *b, sq s);
moveList *pmGetBishopMoves(board *b, sq s);
moveList *pmGetRookMoves(board *b, sq s);
moveList *pmGetQueenMoves(board *b, sq s);
moveList *pmGetKingMoves(board *b, sq s);

// Pawns are special...
moveList *pmGetPawnAttacks(board *b, sq s);
