#include <node_api.h>

#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#include "reward_blob.h"

namespace {

struct State {
    std::uint8_t hunger;
    std::uint8_t bath;
    std::uint8_t funValue;
    std::uint8_t mood;
    std::uint32_t tick;
    std::uint64_t careHash;
};

constexpr std::uint64_t kGolden = 0x9e3779b97f4a7c15ULL;
constexpr std::uint8_t kKeyMask = 0xa5;
constexpr std::array<std::uint8_t, 16> kEncodedKey = {
    0x74, 0x6c, 0xfe, 0x5d, 0x50, 0xea, 0xf7, 0x79,
    0x81, 0x5d, 0xe2, 0x06, 0x88, 0x63, 0xc5, 0x80,
};

static std::uint64_t rotl64(std::uint64_t value, int distance) {
    return (value << distance) | (value >> (64 - distance));
}

static std::uint64_t mix64(std::uint64_t value) {
    value ^= value >> 30;
    value *= 0xbf58476d1ce4e5b9ULL;
    value ^= value >> 27;
    value *= 0x94d049bb133111ebULL;
    value ^= value >> 31;
    return value;
}

static std::uint64_t m0() {
    const std::uint64_t packed = 50ULL | (50ULL << 8) | (50ULL << 16);
    return mix64(0x535549474f544348ULL ^ packed);
}

static State initial_state() {
    return State{50, 50, 50, 0, 0, m0()};
}

static void apply_action(State &s, int action) {
    const std::uint64_t oldHash = s.careHash;
    switch (action) {
        case 1:
            s.hunger = static_cast<std::uint8_t>(s.hunger + 7);
            s.bath = static_cast<std::uint8_t>(s.bath - 3);
            s.funValue = static_cast<std::uint8_t>(s.funValue - 2);
            s.mood ^= 0x13;
            break;
        case 2:
            s.bath = static_cast<std::uint8_t>(s.bath + 11);
            s.hunger = static_cast<std::uint8_t>(s.hunger - 4);
            s.funValue = static_cast<std::uint8_t>(s.funValue - 1);
            s.mood ^= 0x37;
            break;
        case 3:
            s.funValue = static_cast<std::uint8_t>(s.funValue + 13);
            s.hunger = static_cast<std::uint8_t>(s.hunger - 6);
            s.bath = static_cast<std::uint8_t>(s.bath - 5);
            s.mood ^= 0x51;
            break;
        case 4:
            s.hunger = static_cast<std::uint8_t>(s.hunger - 2);
            s.bath = static_cast<std::uint8_t>(s.bath - 2);
            s.funValue = static_cast<std::uint8_t>(s.funValue - 2);
            s.mood = static_cast<std::uint8_t>((s.mood << 3) | (s.mood >> 5));
            break;
        case 5:
            s.funValue ^= 0x5a;
            s.hunger = static_cast<std::uint8_t>(s.hunger + 3);
            s.bath ^= 0x95;
            s.mood = static_cast<std::uint8_t>(s.mood + 17);
            break;
        case 6:
            s.bath ^= 0xbb;
            s.funValue = static_cast<std::uint8_t>(s.funValue + 9);
            s.mood ^= 0xa5;
            break;
        case 7:
            s.hunger ^= 0x1d;
            s.bath = static_cast<std::uint8_t>(s.bath + 4);
            s.funValue = static_cast<std::uint8_t>(s.funValue + 41);
            s.mood ^= 0xfc;
            break;
        default:
            return;
    }
    ++s.tick;
    s.careHash = mix64(
        oldHash ^ static_cast<std::uint64_t>(s.hunger) ^
        (static_cast<std::uint64_t>(s.bath) << 8) ^
        (static_cast<std::uint64_t>(s.funValue) << 16) ^
        (static_cast<std::uint64_t>(s.mood) << 24) ^
        (static_cast<std::uint64_t>(action) << 32) ^
        (static_cast<std::uint64_t>(s.tick) << 40));
}

static std::uint8_t secret_byte(std::size_t index) {
    const auto mask = static_cast<std::uint8_t>(kKeyMask + index * 7);
    return static_cast<std::uint8_t>(kEncodedKey[index] ^ mask);
}

static std::uint64_t sig_word(const State &s) {
    std::uint64_t word = static_cast<std::uint64_t>(s.hunger) |
        (static_cast<std::uint64_t>(s.bath) << 8) |
        (static_cast<std::uint64_t>(s.funValue) << 16) |
        (static_cast<std::uint64_t>(s.mood) << 24) |
        (static_cast<std::uint64_t>(s.tick) << 32);
    word ^= rotl64(s.careHash, 17);
    word = mix64(word ^ 0x8f31a296b057c4d1ULL);
    for (std::size_t i = 0; i < kEncodedKey.size(); ++i) {
        const std::uint64_t lane = static_cast<std::uint64_t>(secret_byte(i)) << ((i & 7U) * 8U);
        word = mix64(word + lane + (i * kGolden));
    }
    return mix64(word ^ rotl64(s.careHash, 39));
}

static std::string signature(const State &s) {
    char text[17] = {};
    std::snprintf(text, sizeof(text), "%016llx", static_cast<unsigned long long>(sig_word(s)));
    return text;
}

static bool equal_signature(const std::string &provided, const std::string &expected) {
    if (provided.size() != expected.size()) return false;
    unsigned int difference = 0;
    for (std::size_t i = 0; i < provided.size(); ++i) {
        difference |= static_cast<unsigned char>(provided[i] ^ expected[i]);
    }
    return difference == 0;
}

static bool read_state(napi_env env, napi_value array, State &s) {
    bool isArray = false;
    std::uint32_t length = 0;
    if (napi_is_array(env, array, &isArray) != napi_ok || !isArray ||
        napi_get_array_length(env, array, &length) != napi_ok || length < 7) return false;
    std::int32_t values[7] = {};
    for (std::uint32_t i = 0; i < 7; ++i) {
        napi_value item;
        if (napi_get_element(env, array, i, &item) != napi_ok ||
            napi_get_value_int32(env, item, &values[i]) != napi_ok) return false;
    }
    const std::uint64_t low = static_cast<std::uint32_t>(values[5]);
    const std::uint64_t high = static_cast<std::uint32_t>(values[6]);
    s = State{
        static_cast<std::uint8_t>(values[0]), static_cast<std::uint8_t>(values[1]),
        static_cast<std::uint8_t>(values[2]), static_cast<std::uint8_t>(values[3]),
        static_cast<std::uint32_t>(values[4]), low | (high << 32),
    };
    return true;
}

static napi_value number(napi_env env, std::uint32_t raw) {
    std::int32_t signedValue;
    std::memcpy(&signedValue, &raw, sizeof(raw));
    napi_value result;
    napi_create_int32(env, signedValue, &result);
    return result;
}

static void write_state(napi_env env, napi_value array, const State &s) {
    const std::int32_t values[7] = {
        s.hunger, s.bath, s.funValue, s.mood, static_cast<std::int32_t>(s.tick),
        static_cast<std::int32_t>(static_cast<std::uint32_t>(s.careHash)),
        static_cast<std::int32_t>(static_cast<std::uint32_t>(s.careHash >> 32)),
    };
    for (std::uint32_t i = 0; i < 7; ++i) {
        napi_value item;
        napi_create_int32(env, values[i], &item);
        napi_set_element(env, array, i, item);
    }
}

static std::string state_csv(const State &s) {
    return std::to_string(s.hunger) + "," + std::to_string(s.bath) + "," +
        std::to_string(s.funValue) + "," + std::to_string(s.mood) + "," +
        std::to_string(static_cast<std::int32_t>(s.tick)) + "," +
        std::to_string(static_cast<std::int32_t>(static_cast<std::uint32_t>(s.careHash))) + "," +
        std::to_string(static_cast<std::int32_t>(static_cast<std::uint32_t>(s.careHash >> 32)));
}

static std::string get_string(napi_env env, napi_value value) {
    std::size_t length = 0;
    napi_get_value_string_utf8(env, value, nullptr, 0, &length);
    std::vector<char> buffer(length + 1, '\0');
    if (length != 0) napi_get_value_string_utf8(env, value, buffer.data(), buffer.size(), &length);
    return std::string(buffer.data(), length);
}

static napi_value js_string(napi_env env, const std::string &value) {
    napi_value result;
    napi_create_string_utf8(env, value.data(), value.size(), &result);
    return result;
}

static std::uint64_t v5() {
    std::uint64_t word = 0;
    for (std::size_t i = 0; i < 8; ++i) {
        const auto mask = static_cast<std::uint8_t>(reward_blob::kHashSalt + i * 19);
        word |= static_cast<std::uint64_t>(reward_blob::kHashBlob[i] ^ mask) << (i * 8);
    }
    return word;
}

static int v0() { return (0x53 ^ 0x46) + 0x12; }
static int v1() { return 0xb9 ^ 0x02; }
static int v2() { return 0x33 ^ 0x79; }
static int v3() { return 0xad ^ 0x64; }
static int v4() { return 0x3c ^ 0x34; }

static bool q2(const State &s) {
    std::uint64_t diff = 0;
    diff |= static_cast<std::uint64_t>(s.hunger ^ v0());
    diff |= static_cast<std::uint64_t>(s.bath ^ v1());
    diff |= static_cast<std::uint64_t>(s.funValue ^ v2());
    diff |= static_cast<std::uint64_t>(s.mood ^ v3());
    diff |= static_cast<std::uint64_t>(s.tick ^ v4());
    diff |= s.careHash ^ v5();
    return diff == 0;
}

static std::string q3(const State &s) {
    std::uint64_t seed = mix64(s.careHash) ^
        mix64((static_cast<std::uint64_t>(s.hunger) << 24) |
              (static_cast<std::uint64_t>(s.bath) << 16) |
              (static_cast<std::uint64_t>(s.funValue) << 8) |
              static_cast<std::uint64_t>(s.mood)) ^ mix64(s.tick);
    std::string output(reward_blob::kCipherSize, '\0');
    for (std::size_t i = 0; i < reward_blob::kCipherSize; ++i) {
        seed = mix64(seed + i + kGolden);
        output[i] = static_cast<char>(reward_blob::kCipher[i] ^ (seed & 0xff));
    }
    return output;
}

static std::string message_for(int action) {
    switch (action) {
        case 1: return "Suisei munches happily.";
        case 2: return "Suisei is sparkling clean.";
        case 3: return "Suisei plays with a tiny comet.";
        case 4: return "Suisei curls up for a comet nap.";
        case 5: return "Suisei hums a strange melody.";
        case 6: return "Something bright passes the window.";
        case 7: return "Something feels out of tune.";
        default: return "Suisei forgot the path of stars.";
    }
}

static std::string note(const State &s) {
    (void)s;
    static constexpr std::uint8_t noise[] = {
        0xef, 0xe8, 0xeb, 0xe8, 0xe0, 0xfe, 0x9e, 0xdc, 0xc6, 0xc9, 0xf8,
        0xc8, 0xcb, 0xc3, 0xf8, 0xd4, 0xce, 0xc0, 0xc9, 0xc6, 0xcb, 0xda,
    };
    std::string result;
    result.reserve(sizeof(noise));
    for (std::uint8_t byte : noise) result.push_back(static_cast<char>(byte ^ 0xa7));
    return result;
}

static napi_value array_result(napi_env env, const State &s, const std::string &message) {
    napi_value result;
    napi_create_array_with_length(env, 3, &result);
    napi_set_element(env, result, 0, js_string(env, signature(s)));
    napi_set_element(env, result, 1, js_string(env, state_csv(s)));
    napi_set_element(env, result, 2, js_string(env, message));
    return result;
}

static napi_value n_a(napi_env env, napi_callback_info info) {
    std::size_t argc = 4;
    napi_value args[4];
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    State s{};
    if (argc < 4 || !read_state(env, args[0], s)) {
        return array_result(env, initial_state(), "Something feels out of tune.");
    }
    std::int32_t action = 0, suspicion = 0;
    napi_get_value_int32(env, args[1], &action);
    const std::string supplied = get_string(env, args[2]);
    napi_get_value_int32(env, args[3], &suspicion);
    std::string message;
    if (!equal_signature(supplied, signature(s))) {
        s = initial_state();
        message = "Something feels out of tune.";
    } else if (suspicion >= 2 && action >= 5) {
        message = "The night is a little too bright.";
    } else if (action < 1 || action > 7) {
        message = "Suisei forgot the path of stars.";
    } else {
        apply_action(s, action);
        message = message_for(action);
    }
    write_state(env, args[0], s);
    return array_result(env, s, message);
}

static napi_value n_b(napi_env env, napi_callback_info info) {
    std::size_t argc = 3;
    napi_value args[3];
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    State s{};
    if (argc < 3 || !read_state(env, args[0], s)) return js_string(env, "Suisei forgot the path of stars.");
    const std::string supplied = get_string(env, args[1]);
    std::int32_t suspicion = 0;
    napi_get_value_int32(env, args[2], &suspicion);
    if (suspicion == 0x5eed) return js_string(env, note(s));
    if (suspicion >= 2) return js_string(env, "Suisei forgot the path of stars.");
    if (!equal_signature(supplied, signature(s))) return js_string(env, "Something feels out of tune.");
    if (!q2(s)) {
        if (s.tick != static_cast<std::uint32_t>(v4())) return js_string(env, "The song order feels wrong.");
        if (s.bath != static_cast<std::uint8_t>(v1())) return js_string(env, "The bath water feels impossible.");
        if (s.careHash != v5()) return js_string(env, "The comet dust still remains.");
        return js_string(env, "Suisei refuses to sing.");
    }
    return js_string(env, q3(s));
}

static napi_value n_c(napi_env env, napi_callback_info info) {
    std::size_t argc = 1;
    napi_value args[1];
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    State s{};
    if (argc < 1 || !read_state(env, args[0], s)) return js_string(env, "");
    if (s.tick == 0 && s.careHash == 0 && s.hunger == 50 && s.bath == 50 &&
        s.funValue == 50 && s.mood == 0) s.careHash = m0();
    write_state(env, args[0], s);
    return js_string(env, signature(s));
}

static napi_value initialize(napi_env env, napi_value exports) {
    const napi_property_descriptor properties[] = {
        {"a", nullptr, n_a, nullptr, nullptr, nullptr, napi_default, nullptr},
        {"b", nullptr, n_b, nullptr, nullptr, nullptr, napi_default, nullptr},
        {"c", nullptr, n_c, nullptr, nullptr, nullptr, napi_default, nullptr},
    };
    napi_define_properties(env, exports, sizeof(properties) / sizeof(properties[0]), properties);
    return exports;
}

}  // namespace

NAPI_MODULE(suigotchi, initialize)
