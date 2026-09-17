#include "bot.h"

#include "zobrist.h"
#include "obfuscate.h"

typedef struct {
    uint64_t veiled_hash;
    uint16_t veiled_move;
    uint8_t ordinal;
} Petal;

static const Petal north[] = {
    {UINT64_C(0x4c76061f4cf773f8), UINT16_C(0xef3f), 0},
    {UINT64_C(0xbd55e5cd8f60bf30), UINT16_C(0x7ed7), 4},
    {UINT64_C(0xe9eee0b0e421d61c), UINT16_C(0x682b), 8},
    {UINT64_C(0x8de59496c6000d94), UINT16_C(0x7048), 12},
    {UINT64_C(0xed5abe1b9ec0957d), UINT16_C(0x9ca7), 16},
    {UINT64_C(0x01b4faa6618bfb5a), UINT16_C(0x2c76), 20},
    {UINT64_C(0xfc5bc9a62efc1692), UINT16_C(0x3ae7), 24},
    {UINT64_C(0xf4194aa2e8390947), UINT16_C(0xd562), 28},
    {UINT64_C(0x02446867db076b93), UINT16_C(0x52e3), 32},
    {UINT64_C(0xcd9b43ceab267fac), UINT16_C(0x143d), 36},
    {UINT64_C(0x3e8a70371f9f83de), UINT16_C(0xb602), 40},
    {UINT64_C(0xb51e1d9ed9614702), UINT16_C(0x4983), 44},
    {UINT64_C(0xcfc48782e036cfd3), UINT16_C(0xdf87), 48},
    {UINT64_C(0x6a6186d12fa7537f), UINT16_C(0x99e3), 52},
    {UINT64_C(0xed8900012698270a), UINT16_C(0x2e6e), 56},
    {UINT64_C(0x08b3cd1bad251798), UINT16_C(0x3abf), 60},
    {UINT64_C(0x1dde7006a80796f4), UINT16_C(0x1d0c), 64},
    {UINT64_C(0x2bc6acb3f9af9874), UINT16_C(0xfd8e), 68},
    {UINT64_C(0xdfbf3c127979244e), UINT16_C(0xfdcb), 72},
    {UINT64_C(0x0ac4b4e5fe782402), UINT16_C(0x29a8), 76},
    {UINT64_C(0x2f5b2bb5d8b7e99d), UINT16_C(0xc4d3), 80},
    {UINT64_C(0x84f8871ce4b9d53f), UINT16_C(0xe5cc), 84},
    {UINT64_C(0x70211d6393bbc304), UINT16_C(0xdcb7), 88},
    {UINT64_C(0xf1debb7835cf29de), UINT16_C(0xdfa8), 92},
    {UINT64_C(0x2041974a4357bbe4), UINT16_C(0xea2a), 96},
};

static const Petal east[] = {
    {UINT64_C(0x6e6dd63952849ff6), UINT16_C(0x2438), 1},
    {UINT64_C(0x1ce4ea49ff0316e3), UINT16_C(0x7bde), 5},
    {UINT64_C(0x16abcc7540d692c8), UINT16_C(0xf707), 9},
    {UINT64_C(0x60761ab182daceaf), UINT16_C(0x29b2), 13},
    {UINT64_C(0x8bf396b1899d6321), UINT16_C(0xa3b4), 17},
    {UINT64_C(0x00b65d5da0f17b4f), UINT16_C(0x7cbc), 21},
    {UINT64_C(0x1a99c8e24c79e90c), UINT16_C(0x0334), 25},
    {UINT64_C(0x80a1f51983d361f5), UINT16_C(0xf523), 29},
    {UINT64_C(0x6229cb44d805b51c), UINT16_C(0x42cb), 33},
    {UINT64_C(0x1352e49287d0021d), UINT16_C(0x81e3), 37},
    {UINT64_C(0xead756c045c4061b), UINT16_C(0x00a8), 41},
    {UINT64_C(0x104bece1e672f1b0), UINT16_C(0xc37b), 45},
    {UINT64_C(0x311ce73a4aa1e532), UINT16_C(0xbe0f), 49},
    {UINT64_C(0xf31789f38bd14e92), UINT16_C(0xb0b0), 53},
    {UINT64_C(0xe7920df5ab6e2325), UINT16_C(0x3b88), 57},
    {UINT64_C(0x95baad7d4d2e28cb), UINT16_C(0x7e9b), 61},
    {UINT64_C(0x31e0f66e86362d1c), UINT16_C(0x70a8), 65},
    {UINT64_C(0xefdf3dafa3f3a66d), UINT16_C(0xda69), 69},
    {UINT64_C(0x1ed5481f8cfdb5ce), UINT16_C(0xd114), 73},
    {UINT64_C(0xd4659ef9e3a11434), UINT16_C(0xb8cf), 77},
    {UINT64_C(0xb2682f075b25993d), UINT16_C(0x2379), 81},
    {UINT64_C(0xf0a891d044d51e9e), UINT16_C(0x8ba5), 85},
    {UINT64_C(0xaffb22ad5430aa9f), UINT16_C(0x14cc), 89},
    {UINT64_C(0x71b90d01dbd314dc), UINT16_C(0xc60b), 93},
    {UINT64_C(0x50f3826de6ab59fc), UINT16_C(0xc7cb), 97},
};

static const Petal south[] = {
    {UINT64_C(0x30ab609a93b98797), UINT16_C(0xac80), 2},
    {UINT64_C(0x0cbb0a09740c4fcd), UINT16_C(0x295d), 6},
    {UINT64_C(0x08dcea7afe2a156a), UINT16_C(0xdeb0), 10},
    {UINT64_C(0xed789844645dc23b), UINT16_C(0x848d), 14},
    {UINT64_C(0x2365a86c6afc5aa1), UINT16_C(0xd8bf), 18},
    {UINT64_C(0xb8e726037261bdd6), UINT16_C(0x573e), 22},
    {UINT64_C(0x26190bc2e261af12), UINT16_C(0xe426), 26},
    {UINT64_C(0x09c7391400eed5a6), UINT16_C(0xadec), 30},
    {UINT64_C(0xd8e40901550d0f73), UINT16_C(0xabbc), 34},
    {UINT64_C(0xb728b72d63ede07e), UINT16_C(0xa311), 38},
    {UINT64_C(0x6e45e7fb08f30e2d), UINT16_C(0xf1ec), 42},
    {UINT64_C(0x957b0fb41b8b7856), UINT16_C(0x2a3d), 46},
    {UINT64_C(0xaeea7d89d33b57c2), UINT16_C(0x66df), 50},
    {UINT64_C(0x8a2ef74713456848), UINT16_C(0x2413), 54},
    {UINT64_C(0xf6e314df97e1c448), UINT16_C(0xc4a8), 58},
    {UINT64_C(0xd1b25e47ed8a5002), UINT16_C(0x958e), 62},
    {UINT64_C(0x2cbf4cd4a4bbdc3e), UINT16_C(0xd19e), 66},
    {UINT64_C(0x50206b9e3e7cb1ba), UINT16_C(0x6997), 70},
    {UINT64_C(0xc8052d721743396b), UINT16_C(0x2f41), 74},
    {UINT64_C(0xbc48f7c19d178213), UINT16_C(0xbacd), 78},
    {UINT64_C(0x874424f18e7c7368), UINT16_C(0x4650), 82},
    {UINT64_C(0x9ceeb55c49b8bd62), UINT16_C(0x6408), 86},
    {UINT64_C(0x17ad2dfad4ff79f6), UINT16_C(0x697d), 90},
    {UINT64_C(0xb7b87af4eaf6bbac), UINT16_C(0xefc7), 94},
    {UINT64_C(0xf72b855248bae9b1), UINT16_C(0xb109), 98},
};

static const Petal west[] = {
    {UINT64_C(0xe812a6f69c94e80c), UINT16_C(0xc626), 3},
    {UINT64_C(0xb11236e063e191bd), UINT16_C(0xaf26), 7},
    {UINT64_C(0xa2ad35b72b73e5cc), UINT16_C(0xb351), 11},
    {UINT64_C(0xea5c156f4ce2f139), UINT16_C(0x95cf), 15},
    {UINT64_C(0x883032f6f174d8c1), UINT16_C(0xa1f8), 19},
    {UINT64_C(0xe766e1614a18fafa), UINT16_C(0x251c), 23},
    {UINT64_C(0x610d50eb0bbe534a), UINT16_C(0x3b0f), 27},
    {UINT64_C(0x726b5211858007be), UINT16_C(0x0bb9), 31},
    {UINT64_C(0x4d2043a865005ae0), UINT16_C(0x68dc), 35},
    {UINT64_C(0x5b8ce211364a8797), UINT16_C(0x2f00), 39},
    {UINT64_C(0xa1066a3b5f1cba15), UINT16_C(0x378d), 43},
    {UINT64_C(0xbafe8da1e78d49b8), UINT16_C(0x1b49), 47},
    {UINT64_C(0xf3a8af2d004e84f4), UINT16_C(0x56bb), 51},
    {UINT64_C(0x8ad5f07c1c4daa83), UINT16_C(0x163c), 55},
    {UINT64_C(0x90bded7a5df4bf7d), UINT16_C(0x7991), 59},
    {UINT64_C(0x1db223f38e965cc3), UINT16_C(0x738c), 63},
    {UINT64_C(0x57e106017b02675c), UINT16_C(0x1506), 67},
    {UINT64_C(0x9bfc9093c744275d), UINT16_C(0x9737), 71},
    {UINT64_C(0x99f13cfc0b539641), UINT16_C(0xd744), 75},
    {UINT64_C(0x651e02a555b03e3b), UINT16_C(0x9f73), 79},
    {UINT64_C(0x1c207167719725bc), UINT16_C(0x6294), 83},
    {UINT64_C(0x18d7e0467347b23c), UINT16_C(0x6ec9), 87},
    {UINT64_C(0xc0c4a70fea17376b), UINT16_C(0xf638), 91},
    {UINT64_C(0x40a0825099a89689), UINT16_C(0xc9cd), 95},
    {UINT64_C(0xf2202712b167ee8b), UINT16_C(0xa795), 99},
};

static void unveil(const Petal *p, uint64_t *hash, RoseMove *move) {
    const uint64_t mask = rose_zobrist_word(9, p->ordinal);
    *hash = p->veiled_hash ^ mask;
    *move = (RoseMove)(p->veiled_move ^ (uint16_t)((mask >> 29) & 0xffffU));
}

ROSE_OBF_CONTROL int rose_bot_decode_entry(unsigned index, uint64_t *hash, RoseMove *move) {
    if (index >= ROSE_PATH_ROUNDS || hash == NULL || move == NULL) return 0;
    const Petal *p;
    switch (index & 3U) {
        case 0: p = &north[index / 4U]; break;
        case 1: p = &east[index / 4U]; break;
        case 2: p = &south[index / 4U]; break;
        default: p = &west[index / 4U]; break;
    }
    unveil(p, hash, move);
    return 1;
}

RoseMove rose_bot_choose(const RoseBoard *board, int *used_hidden_reply) {
    const uint64_t current = rose_position_hash(board);
    if (used_hidden_reply != NULL) *used_hidden_reply = 0;
    for (unsigned i = 0; i < ROSE_PATH_ROUNDS; i++) {
        uint64_t expected;
        RoseMove response;
        rose_bot_decode_entry(i, &expected, &response);
        if (expected == current && rose_move_is_legal(board, response)) {
            if (used_hidden_reply != NULL) *used_hidden_reply = 1;
            return response;
        }
    }
    RoseMove moves[256];
    const size_t count = rose_generate_legal_moves(board, moves, 256);
    RoseMove best = 0;
    int best_score = -2147483647;
    for (size_t i = 0; i < count && i < 256; i++) {
        const int score = rose_move_tactical_score(board, moves[i]);
        if (score > best_score || (score == best_score && moves[i] < best)) {
            best = moves[i]; best_score = score;
        }
    }
    return best;
}

