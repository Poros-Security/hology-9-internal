/*
 * Move definitions
 * Created by thearst3rd on 8/6/2020
 */

#pragma once

#include "chesslib/square.h"
#include "chesslib/piece.h"

typedef struct
{
	sq from;
	sq to;
	pieceType promotion;
} move;

move moveSq(sq from, sq to);
move movePromote(sq from, sq to, pieceType promotion);

uint8_t moveEq(move m1, move m2);

// Gets the UCI notation for a move. Must be freed
char *moveGetUci(move m);
move moveFromUci(char *uci);
