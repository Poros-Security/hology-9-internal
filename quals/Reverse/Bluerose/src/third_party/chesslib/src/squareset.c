/*
 * Square set implementation
 * Created by thearst3rd on 10/31/2020
 */

#include <stdlib.h>

#include "chesslib/squareset.h"

void sqSetSet(sqSet *ss, sq s, uint8_t value)
{
	if (sqEq(s, SQ_INVALID))
		return;

	uint64_t bit = ((uint64_t) 1 << (uint64_t) (sqGetIndex(s)));

	if (value)
		*ss |= bit;
	else
		*ss &= ~bit;
}

uint8_t sqSetGet(sqSet *ss, sq s)
{
	if (sqEq(s, SQ_INVALID))
		return 0;

	return (*ss >> (uint64_t) sqGetIndex(s)) & 1;
}
