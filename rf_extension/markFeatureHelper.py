# Copyright 2025 Adobe
# All Rights Reserved.

# NOTICE: Adobe permits you to use, modify, and distribute this file in
# accordance with the terms of the Adobe license agreement accompanying
# it.

import ezui
import importlib
from AppKit import NSPredicate
from mojo.UI import CurrentFontWindow
from mojo.subscriber import (
    Subscriber, listRegisteredSubscribers,
    registerRoboFontSubscriber, unregisterRoboFontSubscriber)
from pathlib import Path

import markFeatureWriter
importlib.reload(markFeatureWriter)
from markFeatureWriter import MarkFeatureWriter


def make_query(glyph_list):
    query_text = 'Name in {"%s"}' % '", "'.join(glyph_list)
    query = NSPredicate.predicateWithFormat_(query_text)
    CurrentFontWindow().getGlyphCollection().setQuery(query)


def unset_filter():
    cfw = CurrentFontWindow()
    if cfw:
        cfw.getGlyphCollection().setQuery(None)


def find_cmb_marks(f):
    return [g.name for g in f if g.width == 0 and len(g.anchors) > 0]


def cmb_mark_group(f):
    return f.groups.get('COMBINING_MARKS', ())


def compress_user(path):
    '''
    opposite of expanduser
    '''
    user_dir = str(Path('~').expanduser())
    return(f'{path}/'.replace(user_dir, '~'))


class MarkFeatureWriterDefaults(object):
    """
    default values
    These can be overridden via argparse.
    """

    def __init__(self):

        self.input_file = None

        self.trim_tags = False
        self.write_classes = False
        self.write_mkmk = False
        self.indic_format = False

        self.mark_file = 'mark.fea'
        self.mkmk_file = 'mkmk.fea'
        self.mkclass_file = 'markclasses.fea'
        self.abvm_file = 'abvm.fea'
        self.blwm_file = 'blwm.fea'
        self.mkgrp_name = 'COMBINING_MARKS'


class MarkController(Subscriber, ezui.WindowController):

    def build(self):

        self.font = CurrentFont()
        self.cmb_group_exists = cmb_mark_group(self.font)

        tooltip_show = (
            'Show the glyphs contained in an existing COMBINING_MARKS group')
        tooltip_filter = (
            'Filter glyphs identified as combining marks (zero-width, attaching anchors)')
        tooltip_build = (
            'Build COMBINING_MARKS group from selected glyphs')

        tooltip_mark = (
            'Write the mark.fea file -- this is what you’re here for')
        tooltip_mkmk = (
            'Write mkmk.fea file -- optional')
        tooltip_trim = (
            'In the mark.fea file, trim LC/UC from the names of anchors. '
            'This is a very Adobe-specific workflow, read more in the docs.'
        )

        content = f'''
        = TwoColumnForm
        !§ Combining Marks Group @label
        :
        (Show Existing Group)  @button_show_grp_existing ?{tooltip_show}
        :
        (Filter Eligible Glyphs)  @button_show_grp_auto ?{tooltip_filter}
        :
        (Build Group From Selection)  @button_build_grp_sel ?{tooltip_build}

        !§ Feature Files

        :
        [X] Write mark.fea  @checkbox_mark ?{tooltip_mark}
        [ ] Write mkmk.fea  @checkbox_mkmk ?{tooltip_mkmk}
        [ ] Trim UC/LC Tags  @checkbox_trim ?{tooltip_trim}
        (Write Feature File)  @button_write_fea
        '''

        descriptionData = dict(
            content=dict(
                titleColumnWidth=100,
                itemColumnWidth=200
            ),
        )
        self.w = ezui.EZPanel(
            title="Mark Feature Helper",
            content=content,
            descriptionData=descriptionData,
            controller=self
        )

        self.update(self.font)
        self.w.bind('close', self.close_callback)
        self.w.open()

    def update(self, font):
        self.font = font
        self.cmb_group_exists = cmb_mark_group(self.font)
        self.w.getItem('checkbox_mark').enable(0)
        if not self.cmb_group_exists:
            self.w.getItem('button_show_grp_existing').enable(0)
            self.w.getItem('button_write_fea').enable(0)
        else:
            self.w.getItem('button_show_grp_existing').enable(1)
            self.w.getItem('button_write_fea').enable(1)

    def fontDocumentDidBecomeCurrent(self, sender):
        self.update(sender.get('font'))

    def close_callback(self, sender):
        print('goodbye')
        for s in listRegisteredSubscribers(subscriberClassName='MarkController'):
            unregisterRoboFontSubscriber(s)
        self.destroy()

    def destroy(self):
        '''
        undo any font overview filtering when window is closed
        '''
        # each of these are resulting in a RecursionError
        # for s in listRegisteredSubscribers(subscriberClassName='MarkController'):
        #     unregisterRoboFontSubscriber(s)
        # unregisterRoboFontSubscriber(self)
        unset_filter()

    def button_show_grp_existingCallback(self, sender):
        mark_group = cmb_mark_group(self.font)
        make_query(mark_group)

    def button_show_grp_autoCallback(self, sender):
        auto_group = find_cmb_marks(self.font)
        make_query(auto_group)

    def button_build_grp_selCallback(self, sender):
        selection = self.font.selectedGlyphNames
        if selection is not []:
            self.font.groups['COMBINING_MARKS'] = selection
            self.w.getItem('button_write_fea').enable(1)
            self.w.getItem('button_show_grp_existing').enable(1)
        self.update(sender.get('font'))

    def button_build_grp_autoCallback(self, sender):
        auto_group = find_cmb_marks(self.font)
        self.font.groups['COMBINING_MARKS'] = auto_group
        self.w.getItem('button_write_fea').enable(1)

    def checkbox_mkmkCallback(self, sender):
        button = self.w.getItem('button_write_fea')
        if sender.get() == 1:
            # multiple .fea files will be written
            button.setTitle('Write Feature Files')
        else:
            button.setTitle('Write Feature File')

    def button_write_feaCallback(self, sender):
        # need to save the font before we can run mfw
        self.font.save()
        mfw_settings = self.w.content.get()
        mfw_args = MarkFeatureWriterDefaults()
        mfw_args.input_file = self.font.path
        mfw_args.trim_tags = bool(mfw_settings['checkbox_trim'])
        mfw_args.write_mkmk = bool(mfw_settings['checkbox_mkmk'])

        output_dir = compress_user(Path(self.font.path).parent)
        output_msg = '{0}{1} exported to {2}'
        try:
            MarkFeatureWriter(mfw_args)
            if mfw_args.write_mkmk:
                print(output_msg.format(
                    'mark.fea', ' and mkmk.fea', output_dir))
            else:
                print(output_msg.format(
                    'mark.fea', '', output_dir))

        except Exception as e:
            print(f"An error occurred while running MarkFeatureWriter:\n{e}")


f = CurrentFont()
if f is not None:
    registerRoboFontSubscriber(MarkController)
