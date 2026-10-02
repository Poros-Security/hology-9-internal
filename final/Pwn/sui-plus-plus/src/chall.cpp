#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <limits>
#include <string>

extern "C" void dog_default_trick();
extern "C" void rabbit_default_hint();
extern "C" void print_flag();

namespace {

constexpr std::size_t kSlots = 8;
constexpr std::size_t kTextSize = 32;

enum class Kind { Empty, Dog, Cat, Rabbit, Dragon };

void dragon_default_breath();

void copy_text(char (&destination)[kTextSize], const std::string &source) {
    std::memset(destination, 0, sizeof(destination));
    const std::size_t amount = std::min(source.size(), sizeof(destination) - 1);
    std::memcpy(destination, source.data(), amount);
}

bool ask_line(const char *prompt, std::string &answer) {
    std::cout << prompt << std::flush;
    return static_cast<bool>(std::getline(std::cin, answer));
}

bool ask_index(int &index) {
    std::string line;
    if (!ask_line("Animal index: ", line)) return false;
    char *end = nullptr;
    const long parsed = std::strtol(line.c_str(), &end, 10);
    if (end == line.c_str() || *end != '\0' || parsed < 0 || parsed >= static_cast<long>(kSlots)) {
        std::cout << "That slot is outside Sui's little shelter.\n";
        return false;
    }
    index = static_cast<int>(parsed);
    return true;
}

} // namespace

class Animal {
public:
    Animal() { name[0] = '\0'; }
    virtual void speak() = 0;
    virtual ~Animal() = default;

    char name[kTextSize];
};

// These siblings deliberately have the same shape after Animal. On the target
// x86-64 ABI, each function pointer is at object offset 0x48.
class Dog : public Animal {
public:
    Dog() : trick(dog_default_trick) {
        copy_text(nickname, "happy pup");
    }
    void speak() override { std::puts("The dog says: wan wan!"); }

    char nickname[kTextSize];
    void (*trick)();
};

class Cat : public Animal {
public:
    Cat() : useless(UINT64_C(0x4341545f53494c45)) {
        copy_text(mood, "mysteriously unimpressed");
    }
    void speak() override { std::puts("The cat judges you silently."); }

    char mood[kTextSize];
    uint64_t useless;
};

class Rabbit : public Animal {
public:
    Rabbit() : hint(rabbit_default_hint) {
        copy_text(color, "strawberry cream");
    }
    void speak() override { std::puts("The rabbit hops around."); }

    char color[kTextSize];
    void (*hint)();
};

class Dragon : public Animal {
public:
    Dragon() : breath(dragon_default_breath) {
        copy_text(element, "starlight");
    }
    void speak() override { std::puts("The dragon glows with starlight."); }
    void inspect();
    void fire();

    char element[kTextSize];
    void (*breath)();
};

static_assert(sizeof(void (*)()) == 8, "Sui++ targets x86-64 Linux");
static_assert(__builtin_offsetof(Dog, trick) == __builtin_offsetof(Rabbit, hint),
              "Dog and Rabbit function pointers must overlap");
static_assert(__builtin_offsetof(Dog, trick) == __builtin_offsetof(Dragon, breath),
              "Wrong-animal function pointers must overlap");
static_assert(__builtin_offsetof(Dog, trick) == 0x48,
              "Unexpected target ABI: update the challenge layout");

// Export only the two offset anchors and the hidden destination in .dynsym.
// This lets the author solve script recover offsets from the stripped PIE.
// The addresses remain randomized and still require the in-game PIE leak.
extern "C" __attribute__((used, noinline, visibility("default")))
void dog_default_trick() {
    std::puts("The dog spins happily!");
}

extern "C" __attribute__((used, noinline, visibility("default")))
void rabbit_default_hint() {
    std::puts("The rabbit wiggles its ears.");
}

namespace {

void dragon_default_breath() {
    std::puts("A tiny ribbon of starlight curls through the air.");
}

} // namespace

void Dragon::inspect() {
    const auto address = reinterpret_cast<std::uintptr_t>(breath);
    std::printf("Breath pattern: %p\n", reinterpret_cast<void *>(address));
}

void Dragon::fire() {
    if (!breath) {
        std::puts("The dragon coughs a harmless puff of smoke.");
        return;
    }

    std::puts("The dragon takes a deep breath...");
    breath();
}

extern "C" __attribute__((used, noinline, visibility("default")))
void print_flag() {
    FILE *f = std::fopen("flag.txt", "r");
    if (!f) {
        std::puts("flag.txt missing");
        std::exit(1);
    }

    char buf[128] = {};
    if (!std::fgets(buf, sizeof(buf), f)) buf[0] = '\0';
    std::fclose(f);
    std::puts(buf);
}

namespace {

int first_free_slot(Animal *animals[kSlots]) {
    for (std::size_t i = 0; i < kSlots; ++i) {
        if (!animals[i]) return static_cast<int>(i);
    }
    return -1;
}

bool select_occupied(Animal *animals[kSlots], int &index) {
    if (!ask_index(index)) return false;
    if (!animals[index]) {
        std::cout << "That spot is empty.\n";
        return false;
    }
    return true;
}

void adopt(Animal *animals[kSlots], Kind kinds[kSlots], Kind kind) {
    const int slot = first_free_slot(animals);
    if (slot < 0) {
        std::cout << "Every cozy nook is occupied!\n";
        return;
    }

    std::string name;
    const char *prompt = "Little animal's name: ";
    if (!ask_line(prompt, name)) return;

    switch (kind) {
    case Kind::Dog: animals[slot] = new Dog(); break;
    case Kind::Cat: animals[slot] = new Cat(); break;
    case Kind::Rabbit: animals[slot] = new Rabbit(); break;
    case Kind::Dragon: animals[slot] = new Dragon(); break;
    default: return;
    }

    kinds[slot] = kind;
    copy_text(animals[slot]->name, name);
    std::cout << "Welcome home, " << animals[slot]->name << "!\n";
    animals[slot]->speak();
    std::cout << "Your new friend is in slot " << slot << ".\n";
}

void edit_animal(Animal *animals[kSlots], Kind kinds[kSlots]) {
    int index = -1;
    if (!select_occupied(animals, index)) return;

    std::string name;
    if (!ask_line("New name: ", name)) return;
    copy_text(animals[index]->name, name);

    if (kinds[index] == Kind::Dog) {
        auto *dog = static_cast<Dog *>(animals[index]);
        std::string nickname;
        if (!ask_line("New nickname: ", nickname)) return;
        copy_text(dog->nickname, nickname);

        // Harmless naming condition hides the one-field function-pointer edit.
        // The bounded raw read cannot write anywhere outside this Dog object.
        if (std::strcmp(dog->name, "suisei") == 0) {
            std::cout << "Dog trainer mode unlocked!\n";
            std::cout << "New trick pointer bytes: " << std::flush;
            std::cin.read(reinterpret_cast<char *>(&dog->trick), sizeof(dog->trick));
            if (std::cin.gcount() != static_cast<std::streamsize>(sizeof(dog->trick))) return;
            std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
            std::cout << "The dog practices its new trick.\n";
        }
    } else if (kinds[index] == Kind::Cat) {
        auto *cat = static_cast<Cat *>(animals[index]);
        std::string mood;
        if (!ask_line("New mood: ", mood)) return;
        copy_text(cat->mood, mood);
        std::cout << "The cat considers this request.\n";
    } else if (kinds[index] == Kind::Rabbit) {
        auto *rabbit = static_cast<Rabbit *>(animals[index]);
        std::string color;
        if (!ask_line("New fur color: ", color)) return;
        copy_text(rabbit->color, color);
        std::cout << "The rabbit's fur looks extra fluffy.\n";
    } else if (kinds[index] == Kind::Dragon) {
        auto *dragon = static_cast<Dragon *>(animals[index]);
        std::string element;
        if (!ask_line("New sparkle type: ", element)) return;
        copy_text(dragon->element, element);
        std::cout << "The dragon sparkles proudly.\n";
    }
}

void inspect_animal(Animal *animals[kSlots], Kind kinds[kSlots]) {
    int index = -1;
    if (!select_occupied(animals, index)) return;

    if (kinds[index] != Kind::Dragon) {
        std::puts("Sui squints at the animal...");
        std::puts("Are you sure this is a dragon?");
    }
    Dragon *dragon = (Dragon *)animals[index];
    dragon->inspect();
}

void breathe_fire(Animal *animals[kSlots], Kind kinds[kSlots]) {
    int index = -1;
    if (!select_occupied(animals, index)) return;

    if (kinds[index] != Kind::Dragon) {
        std::puts("Sui squints at the animal...");
        std::puts("Are you sure this is a dragon?");
    }

    Dragon *dragon = (Dragon *)animals[index];
    dragon->fire();
}

void release_animal(Animal *animals[kSlots], Kind kinds[kSlots]) {
    int index = -1;
    if (!select_occupied(animals, index)) return;
    delete animals[index];
    animals[index] = nullptr;
    kinds[index] = Kind::Empty;
    std::cout << "Your friend has been safely released.\n";
}

} 
int main() {
    Animal *animals[kSlots] = {};
    Kind kinds[kSlots] = {};

    std::puts("Welcome to Sui++ Animal Shelter!");
    std::puts("Sui loves animals, but the shelter software was written too quickly.");
    std::puts("Every animal is cute, but not every animal should breathe fire...");

    for (;;) {
        std::puts("\n=== Sui++ Animal Shelter ===");
        std::puts("1. Adopt dog");
        std::puts("2. Adopt cat");
        std::puts("3. Adopt rabbit");
        std::puts("4. Adopt dragon");
        std::puts("5. Edit animal");
        std::puts("6. Inspect animal");
        std::puts("7. Breathe fire");
        std::puts("8. Release animal");
        std::puts("9. Exit");

        std::string choice_line;
        if (!ask_line("> ", choice_line)) break;
        const int choice = std::atoi(choice_line.c_str());
        switch (choice) {
        case 1: adopt(animals, kinds, Kind::Dog); break;
        case 2: adopt(animals, kinds, Kind::Cat); break;
        case 3: adopt(animals, kinds, Kind::Rabbit); break;
        case 4: adopt(animals, kinds, Kind::Dragon); break;
        case 5: edit_animal(animals, kinds); break;
        case 6: inspect_animal(animals, kinds); break;
        case 7: breathe_fire(animals, kinds); break;
        case 8: release_animal(animals, kinds); break;
        case 9:
            for (Animal *animal : animals) delete animal;
            std::puts("Sui waves goodbye. Stay fluffy!");
            return 0;
        default: std::puts("Sui doesn't know that shelter chore."); break;
        }
    }

    for (Animal *animal : animals) delete animal;
    return 0;
}
