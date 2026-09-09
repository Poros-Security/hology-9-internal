#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

char *gets(char *str);

#define BUFFER 128

char str_buf[1024];
bool gate_opened = false;

char part1[64];
char part2[64];
char part3[64];

volatile int stage = 0;

void func1();
void func2(long key);
void func3();
bool gate();
void get_flag();
void ignore_me_init_buffering();

void (*next_stage)() = NULL;

void ignore_me_init_buffering() {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
}

void get_flag() {
    FILE *fp = fopen("flag.txt", "r");
    if (fp == NULL) {
        fprintf(stderr, "flag.txt tidak ditemukan\n");
        exit(1);
    }

    char flag[192];
    memset(flag, 0, sizeof(flag));
    fgets(flag, sizeof(flag), fp);
    fclose(fp);

    size_t len = strcspn(flag, "\r\n");
    flag[len] = '\0';
    size_t part_len = len / 3;

    memset(part1, 0, sizeof(part1));
    memset(part2, 0, sizeof(part2));
    memset(part3, 0, sizeof(part3));

    strncpy(part1, flag, part_len);
    strncpy(part2, flag + part_len, part_len);
    strncpy(part3, flag + (2 * part_len), len - (2 * part_len));
}

void func1() {
    if (stage == 2) {
        printf("Part 4 [hidden] :\n" 
               "According to the tales that circulate in Nasha Town "
               "today, the master thief was the world's most skilled trickster. Amidst "
               "countless legends caught betwixt truth and falsehood, their greatest "
               "anecdotes are always laced with lies. He outwitted the most elite guards "
               "in the northern realm with a fake medallion and emptied the governor's "
               "palace, and later, disguised as a special envoy of the Tsar on a secret "
               "inspection, he squeezed the entire treasury out of Viscount Schpekin for "
               "his hospitality. In the popular comedy, A Family of Noblemen: The "
               "Gentlemen Porfiry, staged by the Korolevskiy Troupe. The master thief, "
               "in one of his fleeting appearances, posed before the nobles as a holy "
               "fool who could hear the spirits. Pretending to listen to their "
               "confessions, then weaved their dirty secrets into ballads. Telling the "
               "bards to spread them from tavern to street, so that the weary commoners "
               "might have something to laugh out loud about.\n");
        strcpy(str_buf, part1);
        stage = 3;
    } 

    char buf[BUFFER];
    printf("Input : ");
    gets(buf);
}

void func2(long key) {
    if (stage == 3 && gate_opened && key == 0x1337BEEF) {
        printf("Part 5 [hidden] :\n" 
               "But before these enchanting, unsubstantiated "
               "anecdotes became a public spectacle. The master thief who never lied "
               "gave his partner, who was also of silver blood, a simple vow: He "
               "promised to never put himself in danger, and to never break his word.\n"
               "\"Do not worry for me, Alia. Do not weep for a future that has yet to "
               "arrive.\"\n"
               "\"I know you have your doubts about my friend, but please trust my plan "
               "for now.\"\n"
               "\"Do not worry about me, Alia. If I am indeed the prophesied Ruler of "
               "Elysium,\"\n"
               "\"Then no fate in this world can tear me from the brethren I hold "
               "dear.\"\n"
               "Those were the last words the first master thief left for posterity. "
               "If only the girl who accompanied him could have been like her little "
               "twin sister. Watching the silver thread come to its end, that moment "
               "would surely...\n");
        strcat(str_buf, part2);
    } 

    char buf[BUFFER];
    printf("Input : ");
    gets(buf);
    
}

void func3() {
    if (stage == 0) {
        printf("Part 1 :\n" 
               "Back then, the pitch-dark, muddy currents had not yet crept "
               "into the barren tundra, and even the poor and lowly could sleep "
               "peacefully, protected by the noble fae. But a life of dull toil, lived "
               "without dreams, cannot be termed as suffering at all. Everyone was "
               "assured a small reward for their labor, enough to stay warm. For the "
               "Tsar of all Snezhnaya had a merciful heart as vast as the icy sea, and "
               "was generous even to the small and short-lived. Besides, the noble "
               "princes understood the ancient wisdom that living in unbridled luxury "
               "could corrupt fragile mortal souls. Hence, they alone would not struggle "
               "amidst hunger and cold, for it was they who had to bear the sin of "
               "fullness for the sake of the people. Such compassionate wisdom, what "
               "paragons of virtue! The nobles and commoners alike sang praises to their "
               "ruler's holy name. Praise unto the master of all fae, who, like a stern "
               "father, had painstakingly established a hierarchical system of "
               "governance for all beings living through hardship.\n");
        printf("Part 2 :\n" 
               "But just as the pure white light casts deep shadows, the "
               "nobles' good intentions were often lost on the foolish. And wherever a "
               "high wall was built to guard a treasure, those covetous of heart would "
               "always be tempted to steal it. In the days before the dark torrent that "
               "swallowed up all life arrived, the master of Elysium and ravens barged "
               "into the theater of history. His name was Reed Miller, the man who "
               "would become the master thief renowned across the nations. No one knew "
               "where this master thief had come from, just as no one could uncover his "
               "true nature, hidden beneath the endless lies he spun. Perhaps to mock "
               "those dressed in the sacred white, or perhaps to rouse those living in "
               "festering hunger, poverty, and resentment. The man raised the emblem of "
               "the black raven. He gathered the forsaken and the despised, and "
               "preached bold blasphemies to the very first band of Treasure "
               "Hoarders.\n");
        printf("Part 3 :\n"
               "\"To the poor, to the hungry, to the cold, to the oppressed, and the "
               "abused. To my brothers and sisters, all of you who have found your way "
               "here...\"\n"
               "\"If you have ever suffered injustice at the hands of fate, or if you "
               "have ever wept through the night for your neighbor's pain and "
               "suffering...\"\n"
               "\"If you, too, long for a refuge without fear, and if you, too, dream "
               "of a world where no tears are shed,\"\n"
               "\"Then you, too, must break free of your chains and join us, your "
               "brothers and sisters.\"\n"
               "\"Let the dead bury the dead, and rise to build an Elysium for the "
               "hungry and the poor on the wealth of the high and haughty.\"\n");
         stage = 1;
    } else if (stage == 3){
        printf("Part 6 [hidden] :\n" 
               "Time, however, is ruthless to all. Even that regret "
               "would become an old memory from the time before the master thief "
               "ascended - to his best friend's great remorse - the guillotine steps "
               "and before the young woman who usurped his name hid her face behind a "
               "mask.\n"
               "\"Laugh at their fearful lies, brethren. For they cannot kill Reed "
               "Miller, the master thief.\"\n"
               "\"They have but murdered a single crow, but with tomorrow's light, a "
               "murder of crows shall rise to be at my back\"\n");
        strcat(str_buf, part3);
        printf("%s\n", str_buf);
        return;
    }

    char buf[BUFFER];
    printf("Input : ");
    fgets(buf, sizeof(buf), stdin);
    printf(buf);
   
    if (next_stage != NULL)
        next_stage();
}

bool gate(){
    if (stage != 1) {
        puts("Gate locked.");
        exit(1);
    }
    printf(
        "Gateway to restricted site. "
        "Proceed carefully\n"
    );
    gate_opened = true;
    stage = 2;
    char buf[BUFFER];

    printf("Input password : ");
    gets(buf);

    return gate_opened;
}

int main() {
    ignore_me_init_buffering();
    get_flag();
    printf("================================================\n");
    printf("Hereby lies the history of The Great Thief....\n");
    printf("================================================\n");
    func3();
    return 0;
}
