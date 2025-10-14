#include <stdio.h>
#include <string.h>

int isPalindrome(char str[], int start, int end) {
    if (start>=end) return 1;
    if (str[start]==str[end]) return isPalindrome(str, start+1, end-1);
    else return 0;
}

int main() {
    char word[100];
    printf("Enter a word: ");
    scanf("%s", word);
    int good = isPalindrome(word, 0, strlen(word)-1);
    if (good) printf("Yes\n");
    else printf("No");

    return 0;
}