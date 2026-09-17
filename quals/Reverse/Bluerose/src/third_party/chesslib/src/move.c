/*
 * Move implementation
 * Created by thearst3rd on 8/6/2020
 */

#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>

#include "chesslib/move.h"

move moveSq(sq from, sq to)
{
	return movePromote(from, to, ptEmpty);
}

move movePromote(sq from, sq to, pieceType promotion)
{
	move m;

	m.from = from;
	m.to = to;
	m.promotion = promotion;

	return m;
}

uint8_t moveEq(move m1, move m2)
{
	return sqEq(m1.from, m2.from) && sqEq(m1.to, m2.to) && (m1.promotion == m2.promotion);
}

// Returns the UCI string of the given move. Must be freed.
char *moveGetUci(move m)
{
	char *str;
	char p[2] = {0, 0};
	if (m.promotion)
	{
		p[0] = tolower(pieceTypeGetLetter(m.promotion));
		str = (char *) malloc(6 * sizeof(char));
	}
	else
	{
		str = (char *) malloc(5 * sizeof(char));
	}

	sprintf(str, "%s%s%s", sqGetStr(m.from), sqGetStr(m.to), p);

	return str;
}

// Returns a move from a UCI string
// Note - currently has no error checking...
move moveFromUci(char *uci)
{
	char from[3] = {uci[0], uci[1], 0};
	char to[3] = {uci[2], uci[3], 0};

	pieceType promotion;
	switch (uci[4])
	{
		case 'p': 	// Maybe this should not be here...
			promotion = ptPawn;
			break;

		case 'n':
			promotion = ptKnight;
			break;

		case 'b':
			promotion = ptBishop;
			break;

		case 'r':
			promotion = ptRook;
			break;

		case 'q':
			promotion = ptQueen;
			break;

		case 'k': 	// This is here for chess variants
			promotion = ptKing;
			break;

		default:
			promotion = ptEmpty;
			break;
	}

	move m;
	m.from = sqS(from);
	m.to = sqS(to);
	m.promotion = promotion;
	return m;
}
