import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401
import traceback
import random

'''
           *//////
         ,////////*.                   ..,..              ,,,.
        //////     /////          .&&&&@@@@@&&(      /&&&&@@@&&&&&.      @&&@@@@@@&&&&     @@@@@&&&&@@@@@/    ,@&&@@@@@@@@@     ,@&&&    %&&@*
       /////,      //////.       &&&@.              @&&&,      #&&&(     @&&(      &&&#         /&&&          ,@&&.                &&&@&&&&
       /////       //////*       &&&/              .@&&&       .@&&%     @&&&@@@&&&&@(          /&&&          ,@&&&&&&&&@           (&&&&#
       ,/////      //////        *@&&%,      **     (@&&&,    /&&&@.     @&&(  .%&&&.           /&&&          ,@&&.               &&&@,*@&&&.
        ,//////.   ///,            .%@&&&&&&&@(       ,@@&&&&&&@%.       @&&(     #&&@/         /&&&          ,@&&&&&&&&&&@    ,&&&&.    .&&&@*
          *///////*
             ,/////
                                   .,,,,,,              ,,,,,,.           .,*//(///*,.                   .,*//(///*,.                     .,,,,,,,,.               ,,,,,,,,,,,,,,,,.
                                     /(((((/          /(((((*         ./(((((((((((((((((*           /(((((((((((((((((/,                ,((((((((((,              /((((((((((((((((((((,
                                       ((((((/      ((((((/          /((((((*.    ./(((((*        .((((((((*.    ./(((((((*              ((((((((((((.             /((((/////////(((((((((
                                         /(((((/  /(((((*           ,(((((,              ,       *(((((/             ,((((((           .(((((,  *(((((.            /((((/           ,(((((*
                                           /((((((((((*              (((((((/*,,.               .(((((*               .(((((*         .(((((,    ,(((((.           /((((/           .(((((*
                                             ((((((((                 ,((((((((((((((((/.       ,(((((,                /(((((        .(((((*      /(((((           /((((/          ,((((((.
                                           /((((((((((*                     ,/((((((((((((/     ,(((((,                (((((/       .(((((//////////(((((.         /((((((((((((((((((((/
                                         *(((((/  /(((((*                            /(((((.     ((((((.              /(((((.      .((((((((((((((((((((((.        /(((((((((((((((((,
                                       /(((((/      ((((((*         ,((/*.          ./(((((       /((((((*         ./((((((.       (((((*............/(((((        /((((/       .((((((.
                                     /(((((/         .((((((*       ,(((((((((((((((((((((          /((((((((((((((((((((,        (((((*              /((((/       /((((/         .(((((/
                                   ((((((/              ((((((/        /(((((((((((((((.               ,(((((((((((((/          .(((((*                /(((((      /((((/           *((((((


                                  ,*** .*  *,   ***,  ,*,  *,    */*     .**  .*  ,****  */*    .*  * .***, **** *. *, *. ,//.  ***. ,* ,* .*/,
                                  */,/*  /(     (((( ,/,/* /*   (  ,(    (*/* ,/    (.  (. */   ,(*(/ .(**   **   (**(*/ **  /,.(((* *///   */(
'''




good_images = [
    "https://raw.githubusercontent.com/demisto/content/806a73315034eb4319d58b51d5bfe0ff56e0c3f9/Packs/ctf01/doc_files/until-next.gif"
    ]

bad_images = [
    "https://raw.githubusercontent.com/demisto/content/ctf/Packs/ctf01/doc_files/idola-idola-industries.gif",
    "https://raw.githubusercontent.com/demisto/content/ctf/Packs/ctf01/doc_files/it-doesnt-work-that-way-john-edward.gif",
    "https://raw.githubusercontent.com/demisto/content/ctf/Packs/ctf01/doc_files/lion-king.gif",
    "https://raw.githubusercontent.com/demisto/content/ctf/Packs/ctf01/doc_files/robert-downey-jr-maybe.gif",
    "https://raw.githubusercontent.com/demisto/content/ctf/Packs/ctf01/doc_files/the-rock-look-the-rock-meme.gif"
    ]

HTML_MESSAGE_1 = '''
<img src="%s" alt="Robot">
<div style='font-size:18px;'>
Well Done!!!

Thank you for participating in our XSOAR's workshop. Hope that you have enjoyed the challenge and also gained some knowledge.
Till next time :)


</div>
''' %(good_images[random.randint(0,len(good_images)-1)])

HTML_MESSAGE_BAD = '''
<img src="%s" alt="Error">
<div style='font-size:18px;'>
Nope!!! Try again.
Remember to overwrite the "secret" argument when you are re-running the task. To re-run the task - please click on the 'Run automation now' :)
</div>
''' %(bad_images[random.randint(0,len(bad_images)-1)])

answers = {
    "01" : ["nikesh arora","nikesh","arora","ceo","papa nikesh"],

}

# MAIN FUNCTION #


def main():
    try:
        args = demisto.args()
        #__Error handeling when there is an empty secret or question id__
        if (args.get("secret") == None:
            return_error(f'Please specify Secret and Question ID to proceed with the challange')

        if (args.get("secret").lower() in answers[args.get("01")]):
            return_results({
                'ContentsFormat': EntryFormat.HTML,
                'Type': EntryType.NOTE,
                'Contents': HTML_MESSAGE_1,
                })
        #General Error handeling
        else:
                demisto.results({
                    'Type': entryTypes['error'],
                    'ContentsFormat': formats['html'],
                    'Contents': HTML_MESSAGE_BAD,
                })

    except Exception as exc:  # pylint: disable=W0703
        demisto.error(traceback.format_exc())  # print the traceback
        return_error(f'Failed to execute ERTokenReputation. Error: {str(exc)}')


# ENTRY POINT #


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()

register_module_line('CTF01_Task01', 'end', __line__())
