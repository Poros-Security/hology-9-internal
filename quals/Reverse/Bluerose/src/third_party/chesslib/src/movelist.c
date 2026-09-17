/*
 * Move list implementation
 * Created by thearst3rd on 9/09/2020
 */

#include <stdlib.h>
#include <string.h>

#include "chesslib/movelist.h"

moveList *moveListCreate()
{
	moveList *list = (moveList *) malloc(sizeof(moveList));

	list->head = NULL;
	list->tail = NULL;
	list->size = 0;

	return list;
}

moveListNode *moveListNodeCreate(move move)
{
	moveListNode *node = (moveListNode *) malloc(sizeof(moveListNode));
	node->move = move;
	node->next = NULL;

	return node;
}

void moveListAdd(moveList *list, move move)
{
	moveListNode *node = moveListNodeCreate(move);

	if (list->head == NULL)
	{
		list->head = node;
		list->tail = node;
	}
	else
	{
		moveListNode *prevTail = list->tail;
		prevTail->next = node;
		list->tail = node;
	}
	list->size++;
}

move moveListGet(moveList *list, unsigned int index)
{
	moveListNode *currNode = list->head;
	while (index)
	{
		currNode = currNode->next;
		index--;
	}
	return currNode->move;
}

void moveListUndo(moveList *list)
{
	// This would be easier if I made this a doubly linked...
	if (list == NULL || list->head == NULL)
		return;

	if (list->head->next == NULL)
	{
		free(list->head);
		list->head = NULL;
		list->tail = NULL;
	}
	else
	{
		moveListNode *prev = list->head;
		moveListNode *curr = prev->next;

		while (curr->next)
		{
			prev = curr;
			curr = curr->next;
		}

		free(curr);
		prev->next = NULL;
		list->tail = prev;
	}

	list->size--;
}

// Creates a UCI string from the given movelist. Must be freed
char *moveListGetUciString(moveList *list)
{
	char *str;

	if (list->size == 0)
	{
		str = (char *) malloc(1 * sizeof(char));
		str[0] = 0;
		return str;
	}

	if (list->size == 1)
	{
		str = moveGetUci(list->head->move);
		return str;
	}

	// Count how many bytes this string will take
	// 4 chars per move + 1 space per move - 1 space for the last move + 1 null terminator
	size_t s = 5 * list->size;

	// Add one byte for each promotion character
	for (moveListNode *n = list->head; n; n = n->next)
	{
		if (n->move.promotion != ptEmpty)
			s++;
	}

	str = (char *) malloc(s * sizeof(char));
	char *ptr = str;

	// Load up the string
	for (moveListNode *n = list->head; n; n = n->next)
	{
		char *moveStr = moveGetUci(n->move);
		strcpy(ptr, moveStr);
		ptr += strlen(moveStr);
		*ptr = ' ';
		ptr++;
		free(moveStr);
	}

	// Go back and replace the last space with a null terminator;
	ptr--;
	*ptr = 0;

	return str;
}

void moveListFree(moveList *list)
{
	moveListNode *node = list->head;
	while (node)
	{
		moveListNode *next = node->next;
		free(node);
		node = next;
	}
	free(list);
}
